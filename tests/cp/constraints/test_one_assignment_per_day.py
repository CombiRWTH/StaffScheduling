from datetime import date

import pytest
from ortools.sat.python import cp_model

from scheduling.domain import (
    Employee,
    PlanningMonth,
    PlanningUnit,
    PlanningUnitMembership,
    PlanningUnitType,
    SchedulingDataset,
    Shift,
    ShiftType,
    StaffingDemandRole,
    StaffLevel,
)
from scheduling.solver.cp_sat.constraints.one_assignment_per_day import OneAssignmentPerDay
from scheduling.solver.cp_sat.context import create_context
from scheduling.solver.cp_sat.variables import create_assignment_variables

# --- Shared test data ---

PLANNING_UNIT = PlanningUnit(
    planning_unit_id=1,
    display_name="Station 1",
    type=PlanningUnitType.STATION,
)

# We need at least two shifts to test multiple assignments on a single day
EARLY_SHIFT = Shift(
    shift_id=1,
    code="F",
    type=ShiftType.EARLY,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=360,
    end_minute=820,
    net_work_minutes=460,
)

LATE_SHIFT = Shift(
    shift_id=2,
    code="S",
    type=ShiftType.LATE,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=800,
    end_minute=1260,
    net_work_minutes=460,
)

EMPLOYEE = Employee(
    employee_id=1,
    display_name="Alice",
    staff_level=StaffLevel.PROFESSIONAL,
)

MEMBERSHIP = PlanningUnitMembership(
    planning_unit_id=1,
    employee_id=1,
    valid_from=date(2024, 11, 1),
    valid_until=date(2024, 11, 30),
    staff_level=StaffLevel.PROFESSIONAL,
    is_home=True,
    is_replacement=False,
)


def _dataset() -> SchedulingDataset:
    return SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(EARLY_SHIFT, LATE_SHIFT),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
    )


def _solve_with_forced_assignments(forced_assignments: list[tuple[date, int]]):
    """
    Build a model where the employee is forced to work the specific (date, shift_id) pairs,
    apply the constraint, and solve. Returns the solver status.
    """
    dataset = _dataset()
    ctx = create_context(dataset=dataset)
    create_assignment_variables(ctx)

    # Force the employee to work (or not) on the specific shifts
    for (_employee_id, _unit, assignment_date, shift_id, _level), var in ctx.assignment_variables.items():
        if (assignment_date, shift_id) in forced_assignments:
            ctx.model.add(var == 1)
        else:
            ctx.model.add(var == 0)

    # Apply the constraint
    OneAssignmentPerDay().add_to_model(ctx, params={})

    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


@pytest.mark.integration
def test_feasible_when_one_shift_per_day() -> None:
    # Employee works Early on the 1st and Late on the 2nd
    # (Max 1 shift per day) -> FEASIBLE expected
    forced_assignments = [
        (date(2024, 11, 1), EARLY_SHIFT.shift_id),
        (date(2024, 11, 2), LATE_SHIFT.shift_id),
    ]

    status = _solve_with_forced_assignments(forced_assignments)

    # Pure satisfaction problems usually return FEASIBLE (or OPTIMAL)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_when_two_shifts_same_day() -> None:
    # Employee is forced to work both Early AND Late on the 1st
    # This violates the constraint -> INFEASIBLE expected
    forced_assignments = [
        (date(2024, 11, 1), EARLY_SHIFT.shift_id),
        (date(2024, 11, 1), LATE_SHIFT.shift_id),
    ]

    status = _solve_with_forced_assignments(forced_assignments)

    assert status == cp_model.INFEASIBLE
