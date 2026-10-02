"""The CP-SAT model of one planning month: every hard rule and the three-tier objective.

`build_model` creates one boolean per eligible candidate duty (employee, station, date, shift,
credited qualification) and constrains them over real duty times, including the trusted context
around the month. The objective counts exactly what the schedule check scores, so the solver's
objective value equals the check's weighted total. The rules are implemented here independently of
the check; both share only the policy and the duty times.
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta

from ortools.sat.python import cp_model

from app.domain import (
    POLICY,
    SHIFT_ORDER,
    WORKED_DAYS_WINDOW,
    Assignment,
    AvailabilityType,
    DutyTimes,
    SchedulingDataset,
    Shift,
    ShiftType,
    dates_between,
    duty_times,
    is_working_day,
)
from app.domain.demand import DemandKey
from app.domain.rules import APPROVED_FREE, BLOCKING_AVAILABILITY
from app.solver.diagnostics import DiagnosticSeverity, SolverDiagnostic
from app.solver.models import ObjectiveWeights

# CP-SAT reports objective values as floats; staying below 2**53 keeps every weighted total exact.
MAX_OBJECTIVE = 2**53

type Expr = cp_model.LinearExpr | int


@dataclass(frozen=True, slots=True)
class ScheduleModel:
    model: cp_model.CpModel
    candidates: dict[Assignment, cp_model.IntVar]
    weights: ObjectiveWeights
    diagnostics: tuple[SolverDiagnostic, ...]

    def schedule(self, solver: cp_model.CpSolver) -> tuple[Assignment, ...]:
        """The candidate duties the solved model selects, sorted by date, station, shift and employee."""
        return tuple(
            sorted(
                (duty for duty, variable in self.candidates.items() if solver.value(variable)),
                key=lambda duty: (duty.date, duty.planning_unit_id, duty.shift_id, duty.employee_id),
            )
        )


@dataclass(frozen=True, slots=True, eq=False)
class _Slot:
    """A possible duty of one employee: generated candidates, or a fixed trusted context duty."""

    day: Date
    shift: Shift
    times: DutyTimes
    # Candidate variables over stations and qualifications; empty for a context duty.
    variables: tuple[cp_model.IntVar, ...]

    @property
    def fixed(self) -> bool:
        return not self.variables

    @property
    def expr(self) -> Expr:
        return 1 if self.fixed else sum(self.variables, 0)


def build_model(dataset: SchedulingDataset) -> ScheduleModel:
    """The month's complete model; raises ValueError if its objective could exceed exact integers."""
    return _Builder(dataset).build()


class _Builder:
    def __init__(self, dataset: SchedulingDataset) -> None:
        self.dataset = dataset
        self.month = dataset.planning_month
        self.context = dataset.context
        self.shifts = {shift.shift_id: shift for shift in dataset.shifts}
        self.model = cp_model.CpModel()
        self.candidates: dict[Assignment, cp_model.IntVar] = {}
        # Indices of candidates that fixed context duties alone exclude.
        self.ruled_out: set[int] = set()
        self.diagnostics: list[SolverDiagnostic] = []
        self.health: list[Expr] = []

    def build(self) -> ScheduleModel:
        for employee_slots in self._slots().values():
            ordered = sorted(employee_slots, key=lambda slot: slot.times.start)
            self._one_duty_per_day(ordered)
            self._rest(ordered)
            self._nights(ordered)
            self._work_average(ordered)
            self._replacement_rest(ordered)
            self._six_day_windows(ordered)
            self._backward_transitions(ordered)
        self._staffing()
        deviation, deviation_bound = self._balances()
        surplus, surplus_bound = self._surplus_intermediate()
        weights = self._weights(len(self.health), deviation_bound, surplus_bound)
        self.model.minimize(
            weights.health_events * sum(self.health)
            + weights.balance_deviation_minutes * deviation
            - weights.surplus_intermediate_duties * surplus
        )
        return ScheduleModel(self.model, self.candidates, weights, tuple(self.diagnostics))

    def _diagnose(self, code: str, message: str) -> None:
        self.diagnostics.append(SolverDiagnostic(code=code, severity=DiagnosticSeverity.ERROR, message=message))

    def _slots(self) -> dict[int, list[_Slot]]:
        """Candidate variables of every eligible, available duty, plus the fixed context duties, by employee."""
        duties: list[tuple[Date, Shift, DutyTimes]] = []
        for shift in self.dataset.shifts:
            for day in self.month.dates:
                times = duty_times(day, shift)
                if problem := _pattern_problem(times):
                    self._diagnose("shift.breaks_rules", f"Shift {shift.code} on {day} is never assigned: {problem}")
                else:
                    duties.append((day, shift, times))
        slots: dict[int, list[_Slot]] = {row.employee_id: [] for row in self.dataset.employees}
        for row in self.context.duties:
            shift = self.shifts[row.shift_id]
            slots[row.employee_id].append(_Slot(row.date, shift, duty_times(row.date, shift), ()))
        for employee_id, employee_slots in slots.items():
            memberships = [
                m
                for m in self.dataset.planning_unit_memberships
                if m.employee_id == employee_id and m.planning_unit_id in self.dataset.station_ids
            ]
            for day, shift, times in duties:
                if not self._available(employee_id, day, shift, times):
                    continue
                variables: list[cp_model.IntVar] = []
                for membership in memberships:
                    duty = Assignment(
                        employee_id=employee_id,
                        date=day,
                        planning_unit_id=membership.planning_unit_id,
                        shift_id=shift.shift_id,
                        staff_level=membership.staff_level,
                    )
                    if membership.active_on(day) and duty not in self.candidates:
                        variable = self.model.new_bool_var(
                            f"duty_{employee_id}_{duty.planning_unit_id}_{day:%Y%m%d}_{shift.shift_id}_{duty.staff_level}"
                        )
                        self.candidates[duty] = variable
                        variables.append(variable)
                if variables:
                    employee_slots.append(_Slot(day, shift, times, tuple(variables)))
        return slots

    def _available(self, employee_id: int, day: Date, shift: Shift, times: DutyTimes) -> bool:
        """Whether approved availability allows the duty: nothing blocks a date it touches, every
        restriction of its start date lists its shift, and a night precedes no approved free date."""
        following = day + timedelta(days=1)
        on_day = self.dataset.availability_on(employee_id, day)
        on_following = self.dataset.availability_on(employee_id, following)
        touched = (*on_day, *on_following) if times.touches(following) else on_day
        blocked = {e.availability_type for e in touched}
        restrictions = [e.shift_ids or () for e in on_day if e.availability_type == AvailabilityType.AVAILABLE_ONLY]
        allowed = all(shift.shift_id in shift_ids for shift_ids in restrictions)
        before_free = shift.type == ShiftType.NIGHT and any(e.availability_type in APPROVED_FREE for e in on_following)
        return allowed and not blocked & BLOCKING_AVAILABILITY and not before_free

    def _at_most(self, slots: Sequence[_Slot], limit: int, unless: Sequence[_Slot] = ()) -> None:
        """At most `limit` of the slots are worked, one more for each worked slot of `unless`.

        Fixed slots count as worked. When they alone exhaust the limit and `unless` cannot raise it,
        the open candidates are ruled out, so the staffing diagnostic does not count them.
        """
        open_variables = [variable for slot in slots for variable in slot.variables]
        if not open_variables:
            return
        raising = [variable for slot in unless for variable in slot.variables]
        bound = limit + sum(slot.fixed for slot in unless) - sum(slot.fixed for slot in slots)
        if bound <= 0 and not raising:
            self.ruled_out.update(variable.index for variable in open_variables)
        self.model.add(sum(open_variables) - sum(raising, 0) <= bound)

    def _staffing(self) -> None:
        covering: defaultdict[DemandKey, list[cp_model.IntVar]] = defaultdict(list)
        for duty, variable in self.candidates.items():
            covering[duty.demand_key].append(variable)
        for row in self.dataset.demand_requirements:
            variables = covering[row.demand_key]
            possible = sum(variable.index not in self.ruled_out for variable in variables)
            if possible < row.required_count:
                self._diagnose(
                    "staffing.too_few_candidates",
                    f"Station {row.planning_unit_id} needs {row.required_count} {row.staff_level.value} on "
                    f"{row.date} (shift {row.shift_id}), but only {possible} can work it.",
                )
            self.model.add(sum(variables) >= row.required_count)

    def _one_duty_per_day(self, slots: list[_Slot]) -> None:
        by_day: defaultdict[Date, list[cp_model.IntVar]] = defaultdict(list)
        for slot in slots:
            by_day[slot.day].extend(slot.variables)
        for variables in by_day.values():
            self.model.add_at_most_one(variables)

    def _rest(self, slots: list[_Slot]) -> None:
        """No two duties closer than the minimum rest from one's end to the next one's start."""
        reach = timedelta(minutes=POLICY.min_rest_minutes)
        for index, earlier in enumerate(slots):
            for later in slots[index + 1 :]:
                if later.times.start >= earlier.times.end + reach:
                    break
                self._at_most((earlier, later), 1)

    def _nights(self, slots: list[_Slot]) -> None:
        """At most the policy's consecutive nights, and the full recovery after a block's final night."""
        nights: defaultdict[Date, list[_Slot]] = defaultdict(list)
        for slot in slots:
            if slot.shift.type == ShiftType.NIGHT:
                nights[slot.day].append(slot)
        days = dates_between(self.context.covered_from, self.context.covered_until)
        limit = POLICY.max_consecutive_nights
        for start in range(len(days) - limit):
            window = days[start : start + limit + 1]
            if any(day in self.month for day in window):
                self._at_most([slot for day in window for slot in nights[day]], limit)
        recovery = timedelta(minutes=POLICY.night_recovery_minutes)
        for day, night_slots in list(nights.items()):
            following = nights[day + timedelta(days=1)]
            for night in night_slots:
                for later in slots:
                    if night.times.end <= later.times.start < night.times.end + recovery and later not in following:
                        # A night on the following date makes this one not the final night.
                        self._at_most((night, later), 1, unless=following)

    def _work_average(self, slots: list[_Slot]) -> None:
        """The month's work stays at most the average daily work per Werktag."""
        work = [slot.times.work_minutes * variable for slot in slots for variable in slot.variables]
        if work:
            working_days = sum(is_working_day(day) for day in self.month.dates)
            self.model.add(sum(work) <= POLICY.average_daily_work_minutes * working_days)

    def _replacement_rest(self, slots: list[_Slot]) -> None:
        """Each worked Sunday/holiday of the month gets its own free Werktag of the month inside its window."""
        touched: dict[Date, Expr] = {}

        def works(day: Date) -> Expr:
            if day not in touched:
                touching = [slot for slot in slots if slot.times.touches(day)]
                if any(slot.fixed for slot in touching):
                    touched[day] = 1
                elif not touching:
                    touched[day] = 0
                else:
                    flag = self.model.new_bool_var(f"works_{day:%Y%m%d}")
                    variables = [variable for slot in touching for variable in slot.variables]
                    for variable in variables:
                        self.model.add_implication(variable, flag)
                    self.model.add(flag <= sum(variables))
                    touched[day] = flag
            return touched[day]

        matches: defaultdict[Date, list[cp_model.IntVar]] = defaultdict(list)
        for day in self.month.dates:
            days = POLICY.replacement_days(day)
            if days is None or _is(worked := works(day), 0):
                continue
            options: list[cp_model.IntVar] = []
            for free in self.month.dates:
                if abs((free - day).days) > days or not is_working_day(free) or _is(busy := works(free), 1):
                    continue
                option = self.model.new_bool_var(f"replacement_{day:%Y%m%d}_{free:%Y%m%d}")
                if not _is(busy, 0):
                    self.model.add(option + busy <= 1)
                matches[free].append(option)
                options.append(option)
            self.model.add(sum(options, 0) >= worked)
        for options in matches.values():
            self.model.add_at_most_one(options)

    def _six_day_windows(self, slots: list[_Slot]) -> None:
        worked: defaultdict[Date, list[_Slot]] = defaultdict(list)
        for slot in slots:
            worked[slot.day].append(slot)
        for day in self.month.dates:
            window = [day - timedelta(days=offset) for offset in range(WORKED_DAYS_WINDOW)]
            if not all(worked[d] for d in window):
                continue
            event = self.model.new_bool_var(f"six_days_{day:%Y%m%d}")
            exprs = [sum((slot.expr for slot in worked[d]), 0) for d in window]
            self.model.add(event >= sum(exprs) - (WORKED_DAYS_WINDOW - 1))
            for expr in exprs:
                self.model.add(event <= expr)
            self.health.append(event)

    def _backward_transitions(self, slots: list[_Slot]) -> None:
        """Count successive early/late/night duties that step back in that order; off days do not reset it.

        The comparison starts with the preceding context days. `last[rank]` is 1 exactly when the most
        recent ranked duty so far had that rank.
        """
        ranks = sorted(set(SHIFT_ORDER.values()))
        by_day: defaultdict[Date, list[_Slot]] = defaultdict(list)
        for slot in slots:
            if slot.shift.type in SHIFT_ORDER:
                by_day[slot.day].append(slot)
        last: dict[int, Expr] = dict.fromkeys(ranks, 0)
        for day in dates_between(self.month.start - timedelta(days=POLICY.preceding_context_days), self.month.end):
            ranked = {rank: [s for s in by_day[day] if SHIFT_ORDER[s.shift.type] == rank] for rank in ranks}
            if day not in self.month:
                if worked := [rank for rank in ranks if ranked[rank]]:
                    last = {rank: int(rank == worked[-1]) for rank in ranks}
                continue
            on = {rank: sum((s.expr for s in ranked[rank]), 0) for rank in ranks}
            for rank in ranks:
                for earlier_rank in ranks:
                    if earlier_rank > rank and ranked[rank]:
                        self.health.append(self._both(on[rank], last[earlier_rank]))
            any_ranked = sum(on.values(), 0)
            last = {rank: on[rank] + self._unless(last[rank], any_ranked) for rank in ranks}

    def _both(self, a: Expr, b: Expr) -> Expr:
        """A 0/1 expression that is 1 exactly when both 0/1 expressions are."""
        if _is(a, 0) or _is(b, 0):
            return 0
        if _is(b, 1):
            return a
        both = self.model.new_bool_var("both")
        self.model.add(both <= a)
        self.model.add(both <= b)
        self.model.add(both >= a + b - 1)
        return both

    def _unless(self, kept: Expr, reset: Expr) -> Expr:
        """A 0/1 expression that is `kept` while `reset` is 0, and 0 when it is 1."""
        if _is(kept, 0) or _is(reset, 0):
            return kept
        if _is(kept, 1):
            return 1 - reset
        result = self.model.new_bool_var("unless")
        self.model.add(result <= kept)
        self.model.add(result <= 1 - reset)
        self.model.add(result >= kept - reset)
        return result

    def _balances(self) -> tuple[Expr, int]:
        """Hard monthly balance band per employee; returns the summed absolute deviation and its bound."""
        tolerance = POLICY.balance_tolerance_minutes
        paid: defaultdict[int, list[tuple[cp_model.IntVar, int]]] = defaultdict(list)
        for duty, variable in self.candidates.items():
            if variable.index not in self.ruled_out:
                paid[duty.employee_id].append((variable, self.shifts[duty.shift_id].net_work_minutes))
        deviations: list[Expr] = []
        for account in self.dataset.monthly_work_accounts:
            terms = paid[account.employee_id]
            if not terms:
                if abs(account.balance(0)) > tolerance:
                    self._diagnose(
                        "balance.unreachable",
                        f"Employee {account.employee_id} has no possible duty, but target minus credits is "
                        f"{-account.balance(0)} minutes, beyond ±{tolerance}.",
                    )
                    # An empty clause: the month has no solution.
                    self.model.add_bool_or([])
                deviations.append(abs(account.balance(0)))
                continue
            balance = account.balance(0) + sum(minutes * variable for variable, minutes in terms)
            self.model.add_linear_constraint(balance, -tolerance, tolerance)
            deviation = self.model.new_int_var(0, tolerance, f"deviation_{account.employee_id}")
            self.model.add_abs_equality(deviation, balance)
            deviations.append(deviation)
        return sum(deviations, 0), tolerance * len(deviations)

    def _surplus_intermediate(self) -> tuple[Expr, int]:
        """Intermediate duties beyond the required ones, and how many there could be at most."""
        intermediate = {s.shift_id for s in self.dataset.shifts if s.type == ShiftType.INTERMEDIATE}
        duties = [duty for duty in self.candidates if duty.shift_id in intermediate]
        required = sum(row.required_count for row in self.dataset.demand_requirements if row.shift_id in intermediate)
        employee_days = {(duty.employee_id, duty.date) for duty in duties}
        return sum((self.candidates[duty] for duty in duties), 0) - required, len(employee_days)

    def _weights(self, health_bound: int, deviation_bound: int, surplus_bound: int) -> ObjectiveWeights:
        surplus = 1
        balance = surplus * surplus_bound + 1
        health = balance * deviation_bound + surplus * surplus_bound + 1
        if health * health_bound + balance * deviation_bound + surplus * surplus_bound >= MAX_OBJECTIVE:
            raise ValueError("The month is too large for exact objective weights.")
        return ObjectiveWeights(
            health_events=health, balance_deviation_minutes=balance, surplus_intermediate_duties=surplus
        )


def _pattern_problem(times: DutyTimes) -> str | None:
    """Why one duty's own work segments break the daily rules (ArbZG §§3-4), if they do.

    Work stretches end only at gaps long enough to count as a break part.
    """
    lengths = [int((end - start).total_seconds() // 60) for start, end in times.work]
    gaps = [int((b[0] - a[1]).total_seconds() // 60) for a, b in zip(times.work, times.work[1:], strict=False)]
    work = sum(lengths)
    breaks = sum(gap for gap in gaps if gap >= POLICY.min_break_part_minutes)
    needed = max(
        (
            minutes
            for after, minutes in (
                (POLICY.short_break_after_minutes, POLICY.short_break_minutes),
                (POLICY.long_break_after_minutes, POLICY.long_break_minutes),
            )
            if work > after
        ),
        default=0,
    )
    stretches = [lengths[0]]
    for gap, length in zip(gaps, lengths[1:], strict=True):
        if gap >= POLICY.min_break_part_minutes:
            stretches.append(length)
        else:
            stretches[-1] += length
    if work > POLICY.max_daily_work_minutes:
        return f"{work} minutes of work exceed the daily maximum."
    if breaks < needed:
        return f"{work} minutes of work need {needed} minutes of break, not {breaks}."
    if max(stretches) > POLICY.max_uninterrupted_work_minutes:
        return f"{max(stretches)} minutes of work without a break."
    return None


def _is(expr: Expr, value: int) -> bool:
    """Whether an expression is the plain constant `value`."""
    return isinstance(expr, int) and expr == value
