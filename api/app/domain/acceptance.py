"""The independent schedule check: hard rules and objective scores evaluated on actual assignments.

`check_schedule` never sees solver variables. It recomputes real duty times, accounts and sequences
from the dataset, the trusted context and the assignments, so client- or solver-supplied schedules are
judged alike. It shares only the rule policy and the duty times with the solver.
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta
from enum import StrEnum

from pydantic import computed_field

from app.domain.assignment import Assignment
from app.domain.availability import AvailabilityType
from app.domain.calendar import is_working_day
from app.domain.core import SchedulingBaseModel
from app.domain.dataset import SchedulingDataset
from app.domain.demand import DemandKey, Gap
from app.domain.duty import DutyTimes, duty_times
from app.domain.monthly_work_account import MonthlyWorkAccount
from app.domain.rules import APPROVED_FREE, BLOCKING_AVAILABILITY, POLICY
from app.domain.shift import Shift, ShiftType

# The forward shift order of the health objective; other shift types have no position in it.
SHIFT_ORDER = {ShiftType.EARLY: 0, ShiftType.LATE: 1, ShiftType.NIGHT: 2}
# Fully worked consecutive days counted as one health event.
WORKED_DAYS_WINDOW = 6


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
    """The raw objective tiers, highest priority first; each solver stage reports one of them."""

    gaps: int
    """Required slots that no assignment fills, recomputed from the assignments."""
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
    rules: tuple[Rule, ...]
    """The rules evaluated; anything else is listed in `not_assessed`."""
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
    dataset: SchedulingDataset, assignments: Iterable[Assignment], gaps: Iterable[Gap] = ()
) -> ScheduleCheck:
    """Check the month's assignments and declared gaps against every hard rule and score them.

    Staffing holds when every demand row's shortfall is exactly its declared gap. Malformed
    assignments (unknown references, outside the month, duplicates) are findings and take no part in
    the other checks.
    """
    check = _Check(dataset)
    duties = check.valid_duties(tuple(assignments))
    check.staffing(duties, tuple(gaps))
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
    def __init__(self, dataset: SchedulingDataset) -> None:
        self.dataset = dataset
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
        seen: set[tuple[int, Date, int, int]] = set()
        duties: list[_Duty] = []
        for row in assignments:
            key = (row.employee_id, row.date, row.planning_unit_id, row.shift_id)
            known = (
                row.employee_id in employees
                and row.planning_unit_id in self.dataset.station_ids
                and row.shift_id in self.shifts
            )
            if not known:
                self.fail(Rule.INPUT, "Unknown employee, selected station or shift.", row)
            elif row.date not in self.month:
                self.fail(Rule.INPUT, "The duty starts outside the planning month.", row)
            elif key in seen:
                self.fail(Rule.INPUT, "Duplicate assignment.", row)
            else:
                seen.add(key)
                shift = self.shifts[row.shift_id]
                duties.append(_Duty(row, shift, duty_times(row.date, shift), in_month=True))
        return duties

    def staffing(self, duties: list[_Duty], gaps: tuple[Gap, ...]) -> None:
        declared = Counter[DemandKey]()
        for gap in gaps:
            declared[gap.demand_key] += gap.missing_count
        missing = self.missing(duties)
        for gap in gaps:
            if gap.demand_key not in missing:
                self.fail(
                    Rule.STAFFING,
                    "A gap is declared for a shift without demand.",
                    planning_unit_id=gap.planning_unit_id,
                    date=gap.date,
                    shift_id=gap.shift_id,
                )
        covered = Counter(duty.assignment.demand_key for duty in duties)
        for row in self.dataset.demand_requirements:
            if (gap := declared[row.demand_key]) != missing[row.demand_key]:
                self.fail(
                    Rule.STAFFING,
                    f"{covered[row.demand_key]} of {row.required_count} required {row.staff_level.value} staff, "
                    f"but {gap} declared as gaps.",
                    planning_unit_id=row.planning_unit_id,
                    date=row.date,
                    shift_id=row.shift_id,
                )

    def missing(self, duties: list[_Duty]) -> dict[DemandKey, int]:
        """Every demand row's required slots that no duty fills."""
        covered = Counter(duty.assignment.demand_key for duty in duties)
        return {
            row.demand_key: max(0, row.required_count - covered[row.demand_key])
            for row in self.dataset.demand_requirements
        }

    def eligibility(self, duties: list[_Duty]) -> None:
        memberships = self.dataset.planning_unit_memberships
        for duty in duties:
            row = duty.assignment
            if not any(
                m.employee_id == row.employee_id
                and m.planning_unit_id == row.planning_unit_id
                and m.staff_level == row.staff_level
                and m.active_on(row.date)
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
        """Blocking availability on any date a duty touches, every allowed-shift restriction of its start
        date (several narrow, never widen) and no night before an approved free date."""
        for duty in duties:
            row = duty.assignment
            following = row.date + timedelta(days=1)
            for day in (row.date, following):
                if not duty.times.touches(day):
                    continue
                for entry in self.dataset.availability_on(row.employee_id, day):
                    if entry.availability_type in BLOCKING_AVAILABILITY:
                        self.fail(
                            Rule.AVAILABILITY, f"The duty overlaps {entry.availability_type.value} on {day}.", row
                        )
            for entry in self.dataset.availability_on(row.employee_id, row.date):
                if entry.availability_type == AvailabilityType.AVAILABLE_ONLY and row.shift_id not in (
                    entry.shift_ids or ()
                ):
                    self.fail(Rule.AVAILABILITY, f"Only other shifts are allowed on {row.date}.", row)
            if duty.shift.type == ShiftType.NIGHT and any(
                entry.availability_type in APPROVED_FREE
                for entry in self.dataset.availability_on(row.employee_id, following)
            ):
                self.fail(Rule.AVAILABILITY, f"A night duty may not precede the approved free day {following}.", row)

    def monthly_balance(self, duties: list[_Duty]) -> None:
        tolerance = POLICY.balance_tolerance_minutes
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
        """Daily work and breaks of every duty, and every employee's monthly average per Werktag."""
        total = Counter[int]()
        for duty in duties:
            total[duty.assignment.employee_id] += duty.times.work_minutes
            if problem := _daily_work_problem(duty.times):
                self.fail(Rule.WORK_AND_BREAKS, problem, duty.assignment)
        average = POLICY.average_daily_work_minutes
        working_days = sum(is_working_day(day) for day in self.month.dates)
        for employee_id, minutes in total.items():
            if minutes > average * working_days:
                self.fail(
                    Rule.WORK_AVERAGE,
                    f"{minutes} minutes of work exceed {average} per Werktag on the month's {working_days} Werktage.",
                    employee_id=employee_id,
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
        before = POLICY.preceding_context_days
        first = self.month.start - timedelta(days=before)
        if self.context.covered_from > first:
            self.not_assessed.append(
                NotAssessed(
                    rule=Rule.REST,
                    reason=f"Rest, night, recovery and health scores at the month start need trusted duties of "
                    f"the {before} preceding days.",
                    blocking=True,
                    start=first,
                    end=self.month.start - timedelta(days=1),
                )
            )
        after = POLICY.following_context_days
        if self.context.covered_until < self.month.end + timedelta(days=after):
            self.not_assessed.append(
                NotAssessed(
                    rule=Rule.REST,
                    reason="Rest, night and recovery after the month are checked by the next month's run, "
                    "with this schedule as its preceding context.",
                    blocking=False,
                    start=self.month.end + timedelta(days=1),
                    end=self.month.end + timedelta(days=after),
                )
            )

    def rest(self, timeline: list[_Duty]) -> None:
        minimum = POLICY.min_rest_minutes
        for index, earlier in enumerate(timeline):
            for later in timeline[index + 1 :]:
                gap = earlier.times.minutes_until(later.times)
                if gap >= minimum:
                    break
                if earlier.in_month or later.in_month:
                    self.fail(
                        Rule.REST,
                        f"Only {gap} minutes from the duty of {earlier.assignment.date} to this one."
                        if gap >= 0
                        else f"Overlaps the duty of {earlier.assignment.date}.",
                        later.assignment if later.in_month else earlier.assignment,
                    )

    def nights(self, timeline: list[_Duty]) -> None:
        nights = {duty.assignment.date: duty for duty in timeline if duty.shift.type == ShiftType.NIGHT}
        limit = POLICY.max_consecutive_nights
        for day, night in nights.items():
            run = [night]
            while (run[-1].assignment.date - timedelta(days=1)) in nights:
                run.append(nights[run[-1].assignment.date - timedelta(days=1)])
            if len(run) > limit and any(duty.in_month for duty in run):
                self.fail(Rule.CONSECUTIVE_NIGHTS, f"{len(run)} consecutive night duties.", night.assignment)
            if day + timedelta(days=1) in nights:
                continue
            recovery_end = night.times.end + timedelta(minutes=POLICY.night_recovery_minutes)
            for later in timeline:
                if night.times.end <= later.times.start < recovery_end and (night.in_month or later.in_month):
                    self.fail(
                        Rule.NIGHT_RECOVERY,
                        f"Starts within {POLICY.night_recovery_minutes} minutes of the final night of "
                        f"{night.assignment.date}.",
                        later.assignment if later.in_month else night.assignment,
                    )

    def replacement_rest(self, timeline: list[_Duty]) -> None:
        """Match each worked Sunday/holiday of the month to its own free Werktag of the month inside its window.

        Taking obligations by their window's end and the earliest free date that fits finds a match
        for all of them whenever one exists.
        """
        worked = {day for day in self.month.dates if any(duty.times.touches(day) for duty in timeline)}
        free = [day for day in self.month.dates if day not in worked and is_working_day(day)]
        windows = [
            (day + timedelta(days=days), day - timedelta(days=days), day)
            for day in sorted(worked)
            if (days := POLICY.replacement_days(day)) is not None
        ]
        for end, start, day in sorted(windows):
            match = next((free_day for free_day in free if start <= free_day <= end), None)
            if match is None:
                self.fail(
                    Rule.REPLACEMENT_REST,
                    f"No free Werktag of the month left between {start} and {end} as replacement rest.",
                    employee_id=timeline[0].assignment.employee_id,
                    date=day,
                )
            else:
                free.remove(match)

    def scores(self, duties: list[_Duty], timelines: dict[int, list[_Duty]]) -> ScheduleScores:
        """The objective tiers; backward steps compare with ranked duties from the preceding context days on."""
        lookback = self.month.start - timedelta(days=POLICY.preceding_context_days)
        six_day = backward = 0
        for timeline in timelines.values():
            worked = {duty.assignment.date for duty in timeline}
            six_day += sum(
                all(day - timedelta(days=offset) in worked for offset in range(WORKED_DAYS_WINDOW))
                for day in self.month.dates
            )
            ranked = [duty for duty in timeline if duty.shift.type in SHIFT_ORDER and duty.assignment.date >= lookback]
            backward += sum(
                later.in_month and SHIFT_ORDER[later.shift.type] < SHIFT_ORDER[earlier.shift.type]
                for earlier, later in zip(ranked, ranked[1:], strict=False)
            )
        required = Counter[DemandKey]()
        for row in self.dataset.demand_requirements:
            required[row.demand_key] += row.required_count
        intermediate = Counter(
            duty.assignment.demand_key for duty in duties if duty.shift.type == ShiftType.INTERMEDIATE
        )
        return ScheduleScores(
            gaps=sum(self.missing(duties).values()),
            six_day_windows=six_day,
            backward_transitions=backward,
            balance_deviation_minutes=sum(abs(balance) for _, balance in self.balances(duties)),
            surplus_intermediate_duties=sum(max(0, count - required[key]) for key, count in intermediate.items()),
        )


def _daily_work_problem(times: DutyTimes) -> str | None:
    """Why a duty's own work and break pattern breaks ArbZG §§3-4, if it does."""
    work = times.work_minutes
    if work > POLICY.max_daily_work_minutes:
        return f"{work} minutes of work exceed the daily maximum of {POLICY.max_daily_work_minutes}."
    required = (
        POLICY.long_break_minutes
        if work > POLICY.long_break_after_minutes
        else POLICY.short_break_minutes
        if work > POLICY.short_break_after_minutes
        else 0
    )
    qualifying = sum(gap for gap in times.breaks if gap >= POLICY.min_break_part_minutes)
    if qualifying < required:
        return f"{work} minutes of work need {required} minutes of break, the duty has {qualifying}."
    # A gap shorter than a qualifying break part does not interrupt the work around it.
    run = 0
    for (start, end), gap in zip(times.work, (*times.breaks, None), strict=True):
        run += int((end - start).total_seconds() // 60)
        if run > POLICY.max_uninterrupted_work_minutes:
            return f"More than {POLICY.max_uninterrupted_work_minutes} minutes of work without a break."
        if gap is None or gap >= POLICY.min_break_part_minutes:
            run = 0
    return None
