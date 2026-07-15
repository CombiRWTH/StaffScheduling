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
from scheduling.solver.cp_sat.context import create_context
from scheduling.solver.cp_sat.objectives.rotate_shits_foward import RotateShiftsForward
from scheduling.solver.cp_sat.variables import create_assignment_variables

PLANNING_UNIT = PlanningUnit(
    planning_unit_id=1,
    display_name="Station 1",
    type=PlanningUnitType.STATION,
)

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
    start_minute=820,
    end_minute=1280,
    net_work_minutes=460,
)

NIGHT_SHIFT = Shift(
    shift_id=3,
    code="N",
    type=ShiftType.NIGHT,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=1320,
    end_minute=420,
    net_work_minutes=460,
)

EMPLOYEE = Employee(
    employee_id=1,
    display_name="Alice",
    staff_level=StaffLevel.PROFESSIONAL,
)

MEMBERSHIP = PlanningUnitMembership(
    planning_unit_id=PLANNING_UNIT.planning_unit_id,
    employee_id=EMPLOYEE.employee_id,
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
        shifts=(EARLY_SHIFT, LATE_SHIFT, NIGHT_SHIFT),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
    )


def _penalty_for(worked_assignments: set[tuple[date, int]]) -> float:
    ctx = create_context(dataset=_dataset())
    create_assignment_variables(ctx)

    for (_employee, _unit, assignment_date, shift_id, _level), variable in ctx.assignment_variables.items():
        ctx.model.add(variable == ((assignment_date, shift_id) in worked_assignments))

    penalties = RotateShiftsForward().add_to_model(ctx, params={})
    assert len(penalties) == 1

    penalty = penalties[0]
    assert penalty.objective_id == "rotate_shifts_forward"
    assert penalty.name == "rotations"
    assert penalty.multiplier == 1

    ctx.model.minimize(penalty.multiplier * penalty.expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return solver.objective_value


def test_returns_no_penalties_without_assignment_variables() -> None:
    ctx = create_context(dataset=_dataset())

    assert RotateShiftsForward().add_to_model(ctx, params={}) == ()


@pytest.mark.integration
def test_no_score_without_worked_assignments() -> None:
    assert _penalty_for(set()) == 0


@pytest.mark.integration
@pytest.mark.parametrize(
    ("first_shift_id", "second_shift_id"),
    [
        (EARLY_SHIFT.shift_id, LATE_SHIFT.shift_id),
        (LATE_SHIFT.shift_id, NIGHT_SHIFT.shift_id),
    ],
)
def test_forward_rotation_is_rewarded(first_shift_id: int, second_shift_id: int) -> None:
    worked_assignments = {
        (date(2024, 11, 1), first_shift_id),
        (date(2024, 11, 2), second_shift_id),
    }

    assert _penalty_for(worked_assignments) == -1


@pytest.mark.integration
@pytest.mark.parametrize(
    ("first_shift_id", "second_shift_id"),
    [
        (LATE_SHIFT.shift_id, EARLY_SHIFT.shift_id),
        (NIGHT_SHIFT.shift_id, LATE_SHIFT.shift_id),
        (NIGHT_SHIFT.shift_id, EARLY_SHIFT.shift_id),
    ],
)
def test_backward_rotation_is_penalized(first_shift_id: int, second_shift_id: int) -> None:
    worked_assignments = {
        (date(2024, 11, 1), first_shift_id),
        (date(2024, 11, 2), second_shift_id),
    }

    assert _penalty_for(worked_assignments) == 1


@pytest.mark.integration
def test_rotation_three_days_apart_is_scored() -> None:
    worked_assignments = {
        (date(2024, 11, 1), EARLY_SHIFT.shift_id),
        (date(2024, 11, 4), LATE_SHIFT.shift_id),
    }

    assert _penalty_for(worked_assignments) == -1


@pytest.mark.integration
def test_rotation_more_than_three_days_apart_is_ignored() -> None:
    worked_assignments = {
        (date(2024, 11, 1), EARLY_SHIFT.shift_id),
        (date(2024, 11, 5), LATE_SHIFT.shift_id),
    }

    assert _penalty_for(worked_assignments) == 0
