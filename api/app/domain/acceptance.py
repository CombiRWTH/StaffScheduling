"""The independent schedule check: hard rules and objective scores evaluated on actual assignments.

`check_schedule` never sees solver variables. It recomputes real duty times, accounts and sequences
from the dataset, the trusted context and the assignments, so client- or solver-supplied schedules are
judged alike. Only the small per-duty functions of `app.domain.rules` are shared with the solver.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta
from enum import StrEnum

from pydantic import computed_field

from app.domain.assignment import Assignment
from app.domain.availability import AvailabilityEntry
from app.domain.calendar import dates_between, is_working_day
from app.domain.core import SchedulingBaseModel
from app.domain.dataset import SchedulingDataset
from app.domain.duty import DutyTimes, duty_times
from app.domain.employee import StaffLevel
from app.domain.monthly_work_account import MonthlyWorkAccount
from app.domain.planning_unit import PlanningUnitType
from app.domain.rules import (
    POLICY,
    RulePolicy,
    availability_problem,
    duty_problem,
    replacement_window_days,
    rest_conflict,
)
from app.domain.shift import Shift, ShiftType

# The forward shift order of the health objective; other shift types have no position in it.
SHIFT_ORDER = {ShiftType.EARLY: 0, ShiftType.LATE: 1, ShiftType.NIGHT: 2}
# Fully worked consecutive days counted as one health event.
WORKED_DAYS_WINDOW = 6

type DemandKey = tuple[int, Date, int, StaffLevel]


class CheckStatus(StrEnum):
    """ACCEPTED: every promised rule was checked and holds. REJECTED: a hard rule is violated.
    INCOMPLETE: no violation was found, but a promised check lacked its input."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INCOMPLETE = "incomplete"


class Rule(StrEnum):
    INPUT = "input"
    STAFFING = "staffing"
    ELIGIBILITY = "eligibility"
    ONE_DUTY_PER_DAY = "one_duty_per_day"
    AVAILABILITY = "availability"
    MONTHLY_BALANCE = "monthly_balance"
    WORK_AND_BREAKS = "work_and_breaks"
    WORK_AVERAGE = "work_average"
    REST = "rest"
    CONSECUTIVE_NIGHTS = "consecutive_nights"
    NIGHT_RECOVERY = "night_recovery"
    REPLACEMENT_REST = "replacement_rest"
    ANNUAL_FREE_SUNDAYS = "annual_free_sundays"


class Finding(SchedulingBaseModel):
    """One hard-rule violation of the schedule."""

    rule: Rule
    message: str
    employee_id: int | None = None
    date: Date | None = None
    planning_unit_id: int | None = None
    shift_id: int | None = None


class NotAssessed(SchedulingBaseModel):
    """A rule the input cannot decide, with the exact window and gap; never a pass.

    A blocking gap concerns a check promised for the month and prevents acceptance; a non-blocking one
    names a longer-term or later obligation that this month's input cannot contain.
    """

    rule: Rule
    reason: str
    blocking: bool
    start: Date
    end: Date
    employee_id: int | None = None


class ScheduleScores(SchedulingBaseModel):
    """The raw objective tiers, highest priority first; see the solver documentation for their weights."""

    six_day_windows: int
    backward_transitions: int
    balance_deviation_minutes: int
    surplus_intermediate_duties: int

    @computed_field
    @property
    def health_events(self) -> int:
        return self.six_day_windows + self.backward_transitions


class ScheduleCheck(SchedulingBaseModel):
    status: CheckStatus
    # The rules evaluated; anything else is listed in `not_assessed`.
    rules: tuple[Rule, ...]
    findings: tuple[Finding, ...]
    not_assessed: tuple[NotAssessed, ...]
    scores: ScheduleScores


@dataclass(frozen=True, slots=True)
class _Duty:
    assignment: Assignment
    shift: Shift
    times: DutyTimes
    in_month: bool


ASSESSED = tuple(rule for rule in Rule if rule != Rule.ANNUAL_FREE_SUNDAYS)


def check_schedule(
    dataset: SchedulingDataset, assignments: Iterable[Assignment], policy: RulePolicy = POLICY
) -> ScheduleCheck:
    """Check the month's assignments against every hard rule and score them.

    Malformed assignments (unknown references, outside the month, duplicates) are findings and take
    no part in the other checks.
    """
    check = _Check(dataset, policy)
    duties = check.valid_duties(tuple(assignments))
    check.staffing(duties)
    check.eligibility(duties)
    check.one_duty_per_day(duties)
    check.availability(duties)
    check.monthly_balance(duties)
    check.work(duties)
    timelines = check.timelines(duties)
    check.boundary_coverage()
    for timeline in timelines.values():
        check.rest(timeline)
        check.nights(timeline)
        check.replacement_rest(timeline)
    check.not_assessed.append(
        NotAssessed(
            rule=Rule.ANNUAL_FREE_SUNDAYS,
            reason="At least 15 employment-free Sundays per year need the whole year's duties.",
            blocking=False,
            start=dataset.planning_month.start.replace(month=1, day=1),
            end=dataset.planning_month.start.replace(month=12, day=31),
        )
    )
    status = (
        CheckStatus.REJECTED
        if check.findings
        else CheckStatus.INCOMPLETE
        if any(row.blocking for row in check.not_assessed)
        else CheckStatus.ACCEPTED
    )
    return ScheduleCheck(
        status=status,
        rules=ASSESSED,
        findings=tuple(check.findings),
        not_assessed=tuple(check.not_assessed),
        scores=check.scores(duties, timelines),
    )


class _Check:
    def __init__(self, dataset: SchedulingDataset, policy: RulePolicy) -> None:
        self.dataset = dataset
        self.policy = policy
        self.month = dataset.planning_month
        self.context = dataset.context
        self.shifts = {row.shift_id: row for row in dataset.shifts}
        self.findings: list[Finding] = []
        self.not_assessed: list[NotAssessed] = []

    def fail(
        self,
        rule: Rule,
        message: str,
        assignment: Assignment | None = None,
        *,
        employee_id: int | None = None,
        date: Date | None = None,
        planning_unit_id: int | None = None,
        shift_id: int | None = None,
    ) -> None:
        """Record a violation, located at `assignment` when given."""
        if assignment is not None:
            employee_id, date = assignment.employee_id, assignment.date
            planning_unit_id, shift_id = assignment.planning_unit_id, assignment.shift_id
        self.findings.append(
            Finding(
                rule=rule,
                message=message,
                employee_id=employee_id,
                date=date,
                planning_unit_id=planning_unit_id,
                shift_id=shift_id,
            )
        )

    def valid_duties(self, assignments: tuple[Assignment, ...]) -> list[_Duty]:
        employees = {row.employee_id for row in self.dataset.employees}
        stations = {row.planning_unit_id for row in self.dataset.planning_units if row.type == PlanningUnitType.STATION}
        seen: set[tuple[int, Date, int, int]] = set()
        duties: list[_Duty] = []
        for row in assignments:
            key = (row.employee_id, row.date, row.planning_unit_id, row.shift_id)
            known = row.employee_id in employees and row.planning_unit_id in stations and row.shift_id in self.shifts
            if not known:
                self.fail(Rule.INPUT, "Unknown employee, selected station or shift.", row)
            elif not self.month.start <= row.date <= self.month.end:
                self.fail(Rule.INPUT, "The duty starts outside the planning month.", row)
            elif key in seen:
                self.fail(Rule.INPUT, "Duplicate assignment.", row)
            else:
                seen.add(key)
                shift = self.shifts[row.shift_id]
                duties.append(_Duty(row, shift, duty_times(row.date, shift), in_month=True))
        return duties

    def staffing(self, duties: list[_Duty]) -> None:
        covered = Counter(_demand_key(duty.assignment) for duty in duties)
        for row in self.dataset.demand_requirements:
            key = (row.planning_unit_id, row.date, row.shift_id, row.staff_level)
            if covered[key] < row.required_count:
                self.fail(
                    Rule.STAFFING,
                    f"{covered[key]} of {row.required_count} required {row.staff_level.value} staff.",
                    planning_unit_id=row.planning_unit_id,
                    date=row.date,
                    shift_id=row.shift_id,
                )

    def eligibility(self, duties: list[_Duty]) -> None:
        memberships = self.dataset.planning_unit_memberships
        for duty in duties:
            row = duty.assignment
            if not any(
                m.employee_id == row.employee_id
                and m.planning_unit_id == row.planning_unit_id
                and m.staff_level == row.staff_level
                and m.valid_from <= row.date
                and (m.valid_until is None or row.date <= m.valid_until)
                for m in memberships
            ):
                self.fail(Rule.ELIGIBILITY, f"No active {row.staff_level.value} membership at the station.", row)

    def one_duty_per_day(self, duties: list[_Duty]) -> None:
        counts = Counter((duty.assignment.employee_id, duty.assignment.date) for duty in duties)
        for (employee_id, day), count in counts.items():
            if count > 1:
                message = f"{count} duties start on one date."
                self.fail(Rule.ONE_DUTY_PER_DAY, message, employee_id=employee_id, date=day)

    def availability(self, duties: list[_Duty]) -> None:
        entries: defaultdict[int, defaultdict[Date, list[AvailabilityEntry]]] = defaultdict(lambda: defaultdict(list))
        for row in (*self.dataset.availability, *self.context.availability):
            entries[row.employee_id][row.date].append(row)
        for duty in duties:
            row = duty.assignment
            if problem := availability_problem(row.date, duty.shift, duty.times, entries[row.employee_id]):
                self.fail(Rule.AVAILABILITY, problem, row)

    def monthly_balance(self, duties: list[_Duty]) -> None:
        tolerance = self.policy.balance_tolerance_minutes
        for account, balance in self.balances(duties):
            if abs(balance) > tolerance:
                self.fail(
                    Rule.MONTHLY_BALANCE,
                    f"Balance {balance:+d} minutes (target {account.target_minutes}, credits "
                    f"{account.credited_minutes}) is outside ±{tolerance}.",
                    employee_id=account.employee_id,
                )

    def balances(self, duties: list[_Duty]) -> list[tuple[MonthlyWorkAccount, int]]:
        paid = Counter[int]()
        for duty in duties:
            paid[duty.assignment.employee_id] += duty.shift.net_work_minutes
        return [(row, row.balance(paid[row.employee_id])) for row in self.dataset.monthly_work_accounts]

    def work(self, duties: list[_Duty]) -> None:
        by_employee: defaultdict[int, list[_Duty]] = defaultdict(list)
        for duty in duties:
            by_employee[duty.assignment.employee_id].append(duty)
            if problem := duty_problem(duty.times, self.policy):
                self.fail(Rule.WORK_AND_BREAKS, problem, duty.assignment)
        limit = self.policy.daily_work_minutes
        working_days = sum(is_working_day(day) for day in dates_between(self.month.start, self.month.end))
        for employee_id, own in by_employee.items():
            extended = [duty for duty in own if duty.times.work_minutes > limit]
            if not extended:
                continue
            total = sum(duty.times.work_minutes for duty in own)
            if total > limit * working_days:
                self.fail(
                    Rule.WORK_AVERAGE,
                    f"Duties over {limit} minutes need an average of at most {limit} per Werktag; the month has "
                    f"{total} minutes of work on {working_days} Werktage.",
                    employee_id=employee_id,
                )
            if any(duty.shift.type != ShiftType.NIGHT for duty in extended):
                self.not_assessed.append(
                    NotAssessed(
                        rule=Rule.WORK_AVERAGE,
                        reason="Extended day duties outside night work average over 24 weeks, beyond the month.",
                        blocking=False,
                        start=self.month.start - timedelta(weeks=24),
                        end=self.month.end,
                        employee_id=employee_id,
                    )
                )

    def timelines(self, duties: list[_Duty]) -> dict[int, list[_Duty]]:
        """Every employee's month and context duties in start order."""
        timelines: dict[int, list[_Duty]] = {row.employee_id: [] for row in self.dataset.employees}
        for row in self.context.duties:
            shift = self.shifts[row.shift_id]
            timelines[row.employee_id].append(_Duty(row, shift, duty_times(row.date, shift), in_month=False))
        for duty in duties:
            timelines[duty.assignment.employee_id].append(duty)
        for timeline in timelines.values():
            timeline.sort(key=lambda duty: duty.times.start)
        return timelines

    def boundary_coverage(self) -> None:
        days = self.policy.preceding_context_days
        first = self.month.start - timedelta(days=days)
        if self.context.covered_from > first:
            self.not_assessed.append(
                NotAssessed(
                    rule=Rule.REST,
                    reason=f"Rest, night and recovery rules at the month start need trusted duties of the "
                    f"{days} preceding days.",
                    blocking=True,
                    start=first,
                    end=self.month.start - timedelta(days=1),
                )
            )
        if self.context.covered_until < self.month.end + timedelta(days=days):
            self.not_assessed.append(
                NotAssessed(
                    rule=Rule.REST,
                    reason="Rest, night and recovery after the month are checked by the next month's run, "
                    "with this schedule as its preceding context.",
                    blocking=False,
                    start=self.month.end + timedelta(days=1),
                    end=self.month.end + timedelta(days=days),
                )
            )

    def rest(self, timeline: list[_Duty]) -> None:
        reach = timedelta(minutes=self.policy.min_rest_minutes)
        for index, earlier in enumerate(timeline):
            for later in timeline[index + 1 :]:
                if later.times.start >= earlier.times.end + reach:
                    break
                if (earlier.in_month or later.in_month) and rest_conflict(earlier.times, later.times, self.policy):
                    gap = earlier.times.minutes_until(later.times)
                    self.fail(
                        Rule.REST,
                        f"Only {gap} minutes from the duty of {earlier.assignment.date} to this one."
                        if gap >= 0
                        else f"Overlaps the duty of {earlier.assignment.date}.",
                        later.assignment if later.in_month else earlier.assignment,
                    )

    def nights(self, timeline: list[_Duty]) -> None:
        nights = {duty.assignment.date: duty for duty in timeline if duty.shift.type == ShiftType.NIGHT}
        limit = self.policy.max_consecutive_nights
        for day, night in nights.items():
            run = [night]
            while (run[-1].assignment.date - timedelta(days=1)) in nights:
                run.append(nights[run[-1].assignment.date - timedelta(days=1)])
            if len(run) > limit and any(duty.in_month for duty in run):
                self.fail(Rule.CONSECUTIVE_NIGHTS, f"{len(run)} consecutive night duties.", night.assignment)
            if day + timedelta(days=1) in nights:
                continue
            recovery_end = night.times.end + timedelta(minutes=self.policy.night_recovery_minutes)
            for later in timeline:
                if night.times.end <= later.times.start < recovery_end and (night.in_month or later.in_month):
                    self.fail(
                        Rule.NIGHT_RECOVERY,
                        f"Starts within {self.policy.night_recovery_minutes} minutes of the final night of "
                        f"{night.assignment.date}.",
                        later.assignment if later.in_month else night.assignment,
                    )

    def replacement_rest(self, timeline: list[_Duty]) -> None:
        """Match each worked Sunday/holiday of the month to its own free Werktag inside its window.

        Obligations whose window lies inside the known dates are matched first; the rest are matched
        with what remains and, if unmatched, reported as not assessed.
        """
        if not timeline:
            return
        known = dates_between(self.context.covered_from, self.context.covered_until)
        worked = {day for day in known if any(duty.times.touches(day) for duty in timeline)}
        free = [day for day in known if day not in worked and is_working_day(day)]
        obligations: list[tuple[Date, Date, Date, bool]] = []
        for day in dates_between(self.month.start, self.month.end):
            if day in worked and (days := replacement_window_days(day, self.policy)) is not None:
                start, end = day - timedelta(days=days), day + timedelta(days=days)
                inside = self.context.covered_from <= start and end <= self.context.covered_until
                obligations.append((day, start, end, inside))
        employee_id = timeline[0].assignment.employee_id
        used: set[Date] = set()
        for inside in (True, False):
            for day, start, end, _ in sorted((o for o in obligations if o[3] == inside), key=lambda o: o[2]):
                match = next((d for d in free if start <= d <= end and d not in used), None)
                if match is not None:
                    used.add(match)
                elif inside:
                    self.fail(
                        Rule.REPLACEMENT_REST,
                        f"No free Werktag left between {start} and {end} as replacement rest.",
                        employee_id=employee_id,
                        date=day,
                    )
                else:
                    self.not_assessed.append(
                        NotAssessed(
                            rule=Rule.REPLACEMENT_REST,
                            reason=f"No replacement rest found for {day} inside the known dates; its window "
                            "extends beyond them.",
                            blocking=False,
                            start=start,
                            end=end,
                            employee_id=employee_id,
                        )
                    )

    def scores(self, duties: list[_Duty], timelines: dict[int, list[_Duty]]) -> ScheduleScores:
        six_day = backward = 0
        for timeline in timelines.values():
            worked = {duty.assignment.date for duty in timeline}
            six_day += sum(
                all(day - timedelta(days=offset) in worked for offset in range(WORKED_DAYS_WINDOW))
                for day in dates_between(self.month.start, self.month.end)
            )
            ranked = [duty for duty in timeline if duty.shift.type in SHIFT_ORDER]
            backward += sum(
                later.in_month and SHIFT_ORDER[later.shift.type] < SHIFT_ORDER[earlier.shift.type]
                for earlier, later in zip(ranked, ranked[1:], strict=False)
            )
        required = Counter[DemandKey]()
        for row in self.dataset.demand_requirements:
            required[(row.planning_unit_id, row.date, row.shift_id, row.staff_level)] += row.required_count
        intermediate = Counter(
            _demand_key(duty.assignment) for duty in duties if duty.shift.type == ShiftType.INTERMEDIATE
        )
        return ScheduleScores(
            six_day_windows=six_day,
            backward_transitions=backward,
            balance_deviation_minutes=sum(abs(balance) for _, balance in self.balances(duties)),
            surplus_intermediate_duties=sum(max(0, count - required[key]) for key, count in intermediate.items()),
        )


def _demand_key(row: Assignment) -> DemandKey:
    return (row.planning_unit_id, row.date, row.shift_id, row.staff_level)
