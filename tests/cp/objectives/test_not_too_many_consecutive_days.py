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
from scheduling.solver.cp_sat.objectives.not_too_many_consecutive_days import NotTooManyConsecutiveDays
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

    penalties = NotTooManyConsecutiveDays().add_to_model(ctx, params={})
    assert len(penalties) == 1

    penalty = penalties[0]
    assert penalty.objective_id == "not_too_many_consecutive_days"
    assert penalty.name == "total_too_many_consecutive_days"
    assert penalty.multiplier == 1

    ctx.model.minimize(penalty.multiplier * penalty.expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return solver.objective_value


def test_returns_no_penalties_without_assignment_variables() -> None:
    ctx = create_context(dataset=_dataset())

    assert NotTooManyConsecutiveDays().add_to_model(ctx, params={}) == ()


@pytest.mark.integration
def test_no_penalty_for_five_consecutive_working_days() -> None:
    assert _penalty_for(_date_range(date(2024, 11, 1), 5)) == 0


@pytest.mark.integration
def test_one_penalty_for_six_consecutive_working_days() -> None:
    assert _penalty_for(_date_range(date(2024, 11, 1), 6)) == 1


@pytest.mark.integration
def test_each_six_day_window_is_penalized() -> None:
    assert _penalty_for(_date_range(date(2024, 11, 1), 8)) == 3


@pytest.mark.integration
def test_free_day_separates_consecutive_working_periods() -> None:
    worked_dates = _date_range(date(2024, 11, 1), 6) | _date_range(date(2024, 11, 8), 6)

    assert _penalty_for(worked_dates) == 2


@pytest.mark.integration
def test_penalizes_six_day_window_ending_on_last_day_of_month() -> None:
    assert _penalty_for(_date_range(date(2024, 11, 25), 6)) == 1
