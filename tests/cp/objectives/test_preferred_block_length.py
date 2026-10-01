from datetime import date, timedelta

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
from scheduling.solver.cp_sat.objectives.preferred_block_length import PreferredBlockLength
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
        shifts=(EARLY_SHIFT,),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
    )


def _date_range(start: date, length: int) -> set[date]:
    return {start + timedelta(days=offset) for offset in range(length)}


def _penalty_for(worked_dates: set[date]) -> float:
    ctx = create_context(dataset=_dataset())
    create_assignment_variables(ctx)

    for (_employee, _unit, assignment_date, _shift, _level), variable in ctx.assignment_variables.items():
        ctx.model.add(variable == (assignment_date in worked_dates))

    penalties = PreferredBlockLength().add_to_model(ctx, params={})
    assert len(penalties) == 1

    penalty = penalties[0]
    assert penalty.objective_id == "preferred_block_length"
    assert penalty.name == "total_preferred_blocks"

    ctx.model.minimize(penalty.multiplier * penalty.expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return solver.objective_value


def test_returns_no_penalties_without_assignment_variables() -> None:
    ctx = create_context(dataset=_dataset())

    assert PreferredBlockLength().add_to_model(ctx, params={}) == ()


def test_exact_three_day_block_is_a_reward() -> None:
    ctx = create_context(dataset=_dataset())
    create_assignment_variables(ctx)

    penalties = PreferredBlockLength().add_to_model(ctx, params={})

    assert len(penalties) == 1
    assert penalties[0].multiplier == -1


@pytest.mark.integration
def test_reward_for_exact_three_day_block() -> None:
    assert _penalty_for(_date_range(date(2024, 11, 1), 3)) == -1


@pytest.mark.integration
def test_no_reward_for_block_shorter_than_preferred_length() -> None:
    assert _penalty_for(_date_range(date(2024, 11, 1), 2)) == 0


@pytest.mark.integration
def test_no_reward_for_block_longer_than_preferred_length() -> None:
    assert _penalty_for(_date_range(date(2024, 11, 1), 5)) == 0


@pytest.mark.integration
def test_no_reward_for_blocks_without_exact_three_day_fit() -> None:
    worked_dates = _date_range(date(2024, 11, 1), 2) | _date_range(date(2024, 11, 4), 4)

    assert _penalty_for(worked_dates) == 0


@pytest.mark.integration
def test_no_reward_for_short_block_at_end_of_month() -> None:
    assert _penalty_for(_date_range(date(2024, 11, 29), 2)) == 0


@pytest.mark.integration
def test_no_reward_for_long_consecutive_block() -> None:
    assert _penalty_for(_date_range(date(2024, 11, 1), 8)) == 0
