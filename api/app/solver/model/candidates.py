"""The candidate duties of one planning month and the CP-SAT model they live in.

`CandidateModel` creates one boolean per eligible candidate duty (employee, station, date, shift,
credited qualification) and orders every employee's candidates and trusted context duties into a
timeline over real duty times. Approved availability and each shift's own work and break pattern
decide which candidates exist at all; every other rule is a constraint in `constraints.py`.
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta

from ortools.sat.python import cp_model

from app.domain import (
    POLICY,
    Assignment,
    AvailabilityType,
    DemandRequirement,
    DutyTimes,
    MonthlyWorkAccount,
    SchedulingDataset,
    Shift,
    ShiftType,
    duty_times,
)
from app.domain.rules import APPROVED_FREE, BLOCKING_AVAILABILITY
from app.solver.diagnostics import DiagnosticSeverity, SolverDiagnostic

type Expr = cp_model.LinearExpr | int


@dataclass(frozen=True, slots=True, eq=False)
class Slot:
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


class CandidateModel:
    """The model under construction: its candidates, every employee's timeline and the build diagnostics."""

    def __init__(self, dataset: SchedulingDataset) -> None:
        self.dataset = dataset
        self.month = dataset.planning_month
        self.context = dataset.context
        self._shifts = {shift.shift_id: shift for shift in dataset.shifts}
        self.cp = cp_model.CpModel()
        self.candidates: dict[Assignment, cp_model.IntVar] = {}
        # Indices of candidates that fixed context duties alone exclude.
        self.ruled_out: set[int] = set()
        self.diagnostics: list[SolverDiagnostic] = []
        # Every demand row's unfilled slots, which the staffing rule declares.
        self.gaps: dict[DemandRequirement, cp_model.IntVar] = {}
        # Every employee's slots, ordered by start.
        self.timelines = {
            employee_id: sorted(slots, key=lambda slot: slot.times.start)
            for employee_id, slots in self._slots().items()
        }

    def diagnose(self, code: str, message: str, severity: DiagnosticSeverity = DiagnosticSeverity.ERROR) -> None:
        self.diagnostics.append(SolverDiagnostic(code=code, severity=severity, message=message))

    def at_most(self, slots: Sequence[Slot], limit: int, unless: Sequence[Slot] = ()) -> None:
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
        self.cp.add(sum(open_variables) - sum(raising, 0) <= bound)

    def balance(self, account: MonthlyWorkAccount) -> Expr:
        """The account's monthly balance in minutes over the candidates not ruled out; a constant without any."""
        return account.balance(0) + sum(
            (
                slot.shift.net_work_minutes * variable
                for slot in self.timelines.get(account.employee_id, ())
                for variable in slot.variables
                if variable.index not in self.ruled_out
            ),
            0,
        )

    def logical_and(self, a: Expr, b: Expr) -> Expr:
        """A 0/1 expression that is 1 exactly when both 0/1 expressions are."""
        if is_constant(a, 0) or is_constant(b, 0):
            return 0
        if is_constant(b, 1):
            return a
        both = self.cp.new_bool_var("both")
        self.cp.add(both <= a)
        self.cp.add(both <= b)
        self.cp.add(both >= a + b - 1)
        return both

    def and_not(self, kept: Expr, reset: Expr) -> Expr:
        """A 0/1 expression that is `kept` while `reset` is 0, and 0 when it is 1."""
        if is_constant(kept, 0) or is_constant(reset, 0):
            return kept
        if is_constant(kept, 1):
            return 1 - reset
        result = self.cp.new_bool_var("unless")
        self.cp.add(result <= kept)
        self.cp.add(result <= 1 - reset)
        self.cp.add(result >= kept - reset)
        return result

    def _slots(self) -> dict[int, list[Slot]]:
        """Candidate variables of every eligible, available duty, plus the fixed context duties, by employee."""
        duties: list[tuple[Date, Shift, DutyTimes]] = []
        for shift in self.dataset.shifts:
            for day in self.month.dates:
                times = duty_times(day, shift)
                if problem := _pattern_problem(times):
                    self.diagnose("shift.breaks_rules", f"Shift {shift.code} on {day} is never assigned: {problem}")
                else:
                    duties.append((day, shift, times))
        slots: dict[int, list[Slot]] = {row.employee_id: [] for row in self.dataset.employees}
        for row in self.context.duties:
            shift = self._shifts[row.shift_id]
            slots[row.employee_id].append(Slot(row.date, shift, duty_times(row.date, shift), ()))
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
                        variable = self.cp.new_bool_var(
                            f"duty_{employee_id}_{duty.planning_unit_id}_{day:%Y%m%d}_{shift.shift_id}_{duty.staff_level}"
                        )
                        self.candidates[duty] = variable
                        variables.append(variable)
                if variables:
                    employee_slots.append(Slot(day, shift, times, tuple(variables)))
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


def by_day(slots: Iterable[Slot]) -> defaultdict[Date, list[Slot]]:
    """The slots grouped by their start date."""
    grouped: defaultdict[Date, list[Slot]] = defaultdict(list)
    for slot in slots:
        grouped[slot.day].append(slot)
    return grouped


def is_constant(expr: Expr, value: int) -> bool:
    """Whether an expression is the plain constant `value`."""
    return isinstance(expr, int) and expr == value


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
