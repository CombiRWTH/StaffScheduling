"""The CP-SAT model of one planning month: every hard rule and the three-tier objective.

`build_model` creates one boolean per eligible candidate duty (employee, station, date, shift,
credited qualification) and constrains them over real duty times, including the trusted context
around the month. The objective counts exactly what the schedule check scores, so the solver's
objective value equals the check's weighted total.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta

from ortools.sat.python import cp_model

from app.domain import (
    POLICY,
    SHIFT_ORDER,
    WORKED_DAYS_WINDOW,
    Assignment,
    AvailabilityEntry,
    DutyTimes,
    PlanningUnitType,
    RulePolicy,
    SchedulingDataset,
    Shift,
    ShiftType,
    StaffLevel,
    dates_between,
    duty_times,
    is_working_day,
)
from app.domain.rules import availability_problem, duty_problem, replacement_window_days, rest_conflict
from app.solver.diagnostics import DiagnosticSeverity, SolverDiagnostic
from app.solver.models import ObjectiveWeights

# CP-SAT reports objective values as floats; staying below 2**53 keeps every weighted total exact.
MAX_OBJECTIVE = 2**53

type CandidateKey = tuple[int, int, Date, int, StaffLevel]
type Expr = cp_model.LinearExpr | int


@dataclass(frozen=True, slots=True)
class ScheduleModel:
    model: cp_model.CpModel
    candidates: dict[CandidateKey, cp_model.IntVar]
    weights: ObjectiveWeights
    diagnostics: tuple[SolverDiagnostic, ...]

    def schedule(self, solver: cp_model.CpSolver) -> tuple[Assignment, ...]:
        """The candidate duties the solved model selects, sorted by date, station, shift and employee."""
        return tuple(
            Assignment(employee_id=e, planning_unit_id=u, date=d, shift_id=s, staff_level=level)
            for (e, u, d, s, level), variable in sorted(self.candidates.items(), key=lambda item: item[0][1:4])
            if solver.value(variable)
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


def build_model(dataset: SchedulingDataset, policy: RulePolicy = POLICY) -> ScheduleModel:
    """The month's complete model; raises ValueError if its objective could exceed exact integers."""
    return _Builder(dataset, policy).build()


class _Builder:
    def __init__(self, dataset: SchedulingDataset, policy: RulePolicy) -> None:
        self.dataset = dataset
        self.policy = policy
        self.month = dataset.planning_month
        self.context = dataset.context
        self.shifts = {shift.shift_id: shift for shift in dataset.shifts}
        self.model = cp_model.CpModel()
        self.candidates: dict[CandidateKey, cp_model.IntVar] = {}
        self.diagnostics: list[SolverDiagnostic] = []
        self.health: list[Expr] = []

    def build(self) -> ScheduleModel:
        slots = self._slots()
        self._staffing()
        for employee_slots in slots.values():
            ordered = sorted(employee_slots, key=lambda slot: slot.times.start)
            self._one_duty_per_day(ordered)
            self._rest(ordered)
            self._nights(ordered)
            self._work_average(ordered)
            self._replacement_rest(ordered)
            self._six_day_windows(ordered)
            self._backward_transitions(ordered)
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
        """Candidate variables of every eligible duty, plus the fixed context duties, by employee."""
        stations = [
            unit.planning_unit_id for unit in self.dataset.planning_units if unit.type == PlanningUnitType.STATION
        ]
        duties: list[tuple[Date, Shift, DutyTimes]] = []
        for shift in self.dataset.shifts:
            for day in dates_between(self.month.start, self.month.end):
                times = duty_times(day, shift)
                if problem := duty_problem(times, self.policy):
                    self._diagnose("shift.breaks_rules", f"Shift {shift.code} on {day} is never assigned: {problem}")
                else:
                    duties.append((day, shift, times))
        availability: defaultdict[int, defaultdict[Date, list[AvailabilityEntry]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for row in (*self.dataset.availability, *self.context.availability):
            availability[row.employee_id][row.date].append(row)
        slots: dict[int, list[_Slot]] = {row.employee_id: [] for row in self.dataset.employees}
        for row in self.context.duties:
            shift = self.shifts[row.shift_id]
            slots[row.employee_id].append(_Slot(row.date, shift, duty_times(row.date, shift), ()))
        for employee_id, employee_slots in slots.items():
            memberships = [m for m in self.dataset.planning_unit_memberships if m.employee_id == employee_id]
            fixed = {slot.day: slot for slot in employee_slots}
            for day, shift, times in duties:
                if availability_problem(day, shift, times, availability[employee_id]):
                    continue
                if self._conflicts_with_context(day, shift, times, fixed):
                    continue
                variables: list[cp_model.IntVar] = []
                for station in stations:
                    levels = {
                        m.staff_level
                        for m in memberships
                        if m.planning_unit_id == station
                        and m.valid_from <= day
                        and (m.valid_until is None or day <= m.valid_until)
                    }
                    for level in sorted(levels):
                        key = (employee_id, station, day, shift.shift_id, level)
                        variable = self.model.new_bool_var(f"duty_{'_'.join(map(str, key))}")
                        self.candidates[key] = variable
                        variables.append(variable)
                if variables:
                    employee_slots.append(_Slot(day, shift, times, tuple(variables)))
        return slots

    def _conflicts_with_context(self, day: Date, shift: Shift, times: DutyTimes, fixed: dict[Date, _Slot]) -> bool:
        """Whether the employee's trusted context duties alone rule this duty out, whatever else is chosen.

        Leaving such duties out of the candidates lets the staffing diagnostic name the actual shortage.
        Conflicts that also depend on other month duties stay with the constraints.
        """
        if any(rest_conflict(slot.times, times, self.policy) for slot in fixed.values()):
            return True
        one = timedelta(days=1)

        def fixed_night(on: Date) -> bool:
            return on in fixed and fixed[on].shift.type == ShiftType.NIGHT

        def known_free_of_night(on: Date) -> bool:
            return (
                not self._in_month(on)
                and self.context.covered_from <= on <= self.context.covered_until
                and not fixed_night(on)
            )

        recovery = timedelta(minutes=self.policy.night_recovery_minutes)
        if shift.type == ShiftType.NIGHT:
            before = after = 0
            while fixed_night(day - (before + 1) * one):
                before += 1
            while fixed_night(day + (after + 1) * one):
                after += 1
            if before + after + 1 > self.policy.max_consecutive_nights:
                return True
            # As the final night of its block, nothing fixed may start during its recovery.
            if known_free_of_night(day + one) and any(
                times.end <= slot.times.start < times.end + recovery for slot in fixed.values()
            ):
                return True
        # Within the recovery after a fixed final night.
        return any(
            slot.shift.type == ShiftType.NIGHT
            and known_free_of_night(slot.day + one)
            and slot.times.end <= times.start < slot.times.end + recovery
            for slot in fixed.values()
        )

    def _staffing(self) -> None:
        covering: defaultdict[tuple[int, Date, int, StaffLevel], list[cp_model.IntVar]] = defaultdict(list)
        for (_, station, day, shift_id, level), variable in self.candidates.items():
            covering[(station, day, shift_id, level)].append(variable)
        for row in self.dataset.demand_requirements:
            variables = covering[(row.planning_unit_id, row.date, row.shift_id, row.staff_level)]
            if len(variables) < row.required_count:
                self._diagnose(
                    "staffing.too_few_candidates",
                    f"Station {row.planning_unit_id} needs {row.required_count} {row.staff_level.value} on "
                    f"{row.date} (shift {row.shift_id}), but only {len(variables)} can work it.",
                )
            self.model.add(sum(variables) >= row.required_count)

    def _one_duty_per_day(self, slots: list[_Slot]) -> None:
        by_day: defaultdict[Date, list[cp_model.IntVar]] = defaultdict(list)
        for slot in slots:
            by_day[slot.day].extend(slot.variables)
        for variables in by_day.values():
            self.model.add_at_most_one(variables)

    def _rest(self, slots: list[_Slot]) -> None:
        reach = timedelta(minutes=self.policy.min_rest_minutes)
        for index, earlier in enumerate(slots):
            for later in slots[index + 1 :]:
                if later.times.start >= earlier.times.end + reach:
                    break
                if not (earlier.fixed and later.fixed) and rest_conflict(earlier.times, later.times, self.policy):
                    self.model.add(earlier.expr + later.expr <= 1)

    def _nights(self, slots: list[_Slot]) -> None:
        """At most the policy's consecutive nights, and the full recovery after a block's final night."""
        nights: defaultdict[Date, list[_Slot]] = defaultdict(list)
        for slot in slots:
            if slot.shift.type == ShiftType.NIGHT:
                nights[slot.day].append(slot)

        def on(day: Date) -> Expr:
            return sum((slot.expr for slot in nights[day]), 0)

        days = dates_between(self.context.covered_from, self.context.covered_until)
        limit = self.policy.max_consecutive_nights
        for start in range(len(days) - limit):
            window = days[start : start + limit + 1]
            if any(self._in_month(day) for day in window) and not all(s.fixed for d in window for s in nights[d]):
                self.model.add(sum(on(day) for day in window) <= limit)
        recovery = timedelta(minutes=self.policy.night_recovery_minutes)
        for day, night_slots in list(nights.items()):
            following = day + timedelta(days=1)
            if following > self.context.covered_until:
                continue
            for night in night_slots:
                for later in slots:
                    if not night.times.end <= later.times.start < night.times.end + recovery:
                        continue
                    if later in nights[following]:
                        continue
                    involved = (night, later, *nights[following])
                    if not all(slot.fixed for slot in involved):
                        self.model.add(night.expr + later.expr - on(following) <= 1)

    def _work_average(self, slots: list[_Slot]) -> None:
        """Duties beyond eight hours of work require the month's average to stay at eight per Werktag."""
        limit = self.policy.daily_work_minutes
        month = [slot for slot in slots if not slot.fixed]
        extended = [variable for slot in month if slot.times.work_minutes > limit for variable in slot.variables]
        if not extended:
            return
        uses_extended = self.model.new_bool_var("uses_extended_duty")
        for variable in extended:
            self.model.add_implication(variable, uses_extended)
        working_days = sum(is_working_day(day) for day in dates_between(self.month.start, self.month.end))
        total = sum((slot.times.work_minutes * slot.expr for slot in month), 0)
        # Without an extended duty the bound relaxes by the most work the month's candidates could add.
        slack = sum(slot.times.work_minutes for slot in month)
        self.model.add(total <= limit * working_days + slack * (1 - uses_extended))

    def _replacement_rest(self, slots: list[_Slot]) -> None:
        """Each worked Sunday/holiday of the month whose window lies in known dates gets its own free Werktag."""
        start, end = self.context.covered_from, self.context.covered_until
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
        for day in dates_between(self.month.start, self.month.end):
            days = replacement_window_days(day, self.policy)
            if days is None or not start <= day - timedelta(days=days) or day + timedelta(days=days) > end:
                continue
            if _is(worked := works(day), 0):
                continue
            options: list[cp_model.IntVar] = []
            for free in dates_between(day - timedelta(days=days), day + timedelta(days=days)):
                if free == day or not is_working_day(free) or _is(busy := works(free), 1):
                    continue
                option = self.model.new_bool_var(f"replacement_{day:%Y%m%d}_{free:%Y%m%d}")
                if not _is(busy, 0):
                    self.model.add(option + busy <= 1)
                matches[free].append(option)
                options.append(option)
            self.model.add(sum(options) >= worked)
        for options in matches.values():
            self.model.add_at_most_one(options)

    def _six_day_windows(self, slots: list[_Slot]) -> None:
        worked: defaultdict[Date, list[_Slot]] = defaultdict(list)
        for slot in slots:
            worked[slot.day].append(slot)
        for day in dates_between(self.month.start, self.month.end):
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

        `last[rank]` is 1 exactly when the most recent ranked duty so far had that rank.
        """
        ranks = sorted(set(SHIFT_ORDER.values()))
        by_day: defaultdict[Date, list[_Slot]] = defaultdict(list)
        for slot in slots:
            if slot.shift.type in SHIFT_ORDER:
                by_day[slot.day].append(slot)
        last: dict[int, Expr] = dict.fromkeys(ranks, 0)
        for day in dates_between(self.context.covered_from, self.month.end):
            ranked = {rank: [s for s in by_day[day] if SHIFT_ORDER[s.shift.type] == rank] for rank in ranks}
            if day < self.month.start:
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
        tolerance = self.policy.balance_tolerance_minutes
        paid: defaultdict[int, list[tuple[cp_model.IntVar, int]]] = defaultdict(list)
        for (employee_id, _, _, shift_id, _), variable in self.candidates.items():
            paid[employee_id].append((variable, self.shifts[shift_id].net_work_minutes))
        deviations: list[Expr] = []
        for account in self.dataset.monthly_work_accounts:
            terms = paid[account.employee_id]
            balance = account.balance(0) + sum(minutes * variable for variable, minutes in terms)
            if not terms:
                if abs(account.balance(0)) > tolerance:
                    self._diagnose(
                        "balance.unreachable",
                        f"Employee {account.employee_id} has no possible duty, but target minus credits is "
                        f"{-account.balance(0)} minutes, beyond ±{tolerance}.",
                    )
                    self.model.add(sum([]) >= 1)
                deviations.append(abs(account.balance(0)))
                continue
            self.model.add_linear_constraint(balance, -tolerance, tolerance)
            deviation = self.model.new_int_var(0, tolerance, f"deviation_{account.employee_id}")
            self.model.add_abs_equality(deviation, balance)
            deviations.append(deviation)
        return sum(deviations, 0), tolerance * len(deviations)

    def _surplus_intermediate(self) -> tuple[Expr, int]:
        """Intermediate duties beyond the required ones, and how many there could be at most."""
        intermediate = {s.shift_id for s in self.dataset.shifts if s.type == ShiftType.INTERMEDIATE}
        variables = [variable for key, variable in self.candidates.items() if key[3] in intermediate]
        required = sum(row.required_count for row in self.dataset.demand_requirements if row.shift_id in intermediate)
        employee_days = {(key[0], key[2]) for key in self.candidates if key[3] in intermediate}
        return sum(variables, 0) - required, len(employee_days)

    def _weights(self, health_bound: int, deviation_bound: int, surplus_bound: int) -> ObjectiveWeights:
        surplus = 1
        balance = surplus * surplus_bound + 1
        health = balance * deviation_bound + surplus * surplus_bound + 1
        if health * health_bound + balance * deviation_bound + surplus * surplus_bound >= MAX_OBJECTIVE:
            raise ValueError("The month is too large for exact objective weights.")
        return ObjectiveWeights(
            health_events=health, balance_deviation_minutes=balance, surplus_intermediate_duties=surplus
        )

    def _in_month(self, day: Date) -> bool:
        return self.month.start <= day <= self.month.end


def _is(expr: Expr, value: int) -> bool:
    """Whether an expression is the plain constant `value`."""
    return isinstance(expr, int) and expr == value
