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
from scheduling.solver.cp_sat.objectives.prefer_own_planning_unit import PreferOwnPlanningUnit
from scheduling.solver.cp_sat.variables import create_assignment_variables

HOME_STATION = PlanningUnit(
    planning_unit_id=1,
    display_name="Station 1",
    type=PlanningUnitType.STATION,
)

OTHER_STATION = PlanningUnit(
    planning_unit_id=2,
    display_name="Station 2",
    type=PlanningUnitType.STATION,
)

SHARED_POOL = PlanningUnit(
    planning_unit_id=3,
    display_name="Shared Pool",
    type=PlanningUnitType.SHARED_POOL,
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


def _membership(
    planning_unit: PlanningUnit,
    *,
    valid_from: date = date(2024, 11, 1),
    valid_until: date | None = date(2024, 11, 30),
    is_home: bool,
    is_replacement: bool,
) -> PlanningUnitMembership:
    return PlanningUnitMembership(
        planning_unit_id=planning_unit.planning_unit_id,
        employee_id=EMPLOYEE.employee_id,
        valid_from=valid_from,
        valid_until=valid_until,
        staff_level=StaffLevel.PROFESSIONAL,
        is_home=is_home,
        is_replacement=is_replacement,
    )


def _dataset(memberships: tuple[PlanningUnitMembership, ...]) -> SchedulingDataset:
    return SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(HOME_STATION, OTHER_STATION, SHARED_POOL),
        plans=(),
        shifts=(EARLY_SHIFT,),
        employees=(EMPLOYEE,),
        planning_unit_memberships=memberships,
    )


def _penalty_for(
    *,
    memberships: tuple[PlanningUnitMembership, ...],
    worked_assignments: set[tuple[int, date]],
) -> float:
    ctx = create_context(dataset=_dataset(memberships))
    create_assignment_variables(ctx)

    for (_employee, planning_unit_id, assignment_date, _shift, _level), variable in ctx.assignment_variables.items():
        ctx.model.add(variable == ((planning_unit_id, assignment_date) in worked_assignments))

    penalties = PreferOwnPlanningUnit().add_to_model(ctx, params={})
    assert len(penalties) == 1

    penalty = penalties[0]
    assert penalty.objective_id == "prefer_own_planning_unit"
    assert penalty.name == "prefer_own_planning_unit_penalty"
    assert penalty.multiplier == 1

    ctx.model.minimize(penalty.multiplier * penalty.expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return solver.objective_value


def test_returns_no_penalties_without_assignment_variables() -> None:
    ctx = create_context(dataset=_dataset(()))

    assert PreferOwnPlanningUnit().add_to_model(ctx, params={}) == ()


@pytest.mark.integration
def test_no_penalty_for_assignment_to_active_home_station() -> None:
    memberships = (_membership(HOME_STATION, is_home=True, is_replacement=False),)

    assert (
        _penalty_for(
            memberships=memberships,
            worked_assignments={(HOME_STATION.planning_unit_id, date(2024, 11, 1))},
        )
        == 0
    )


@pytest.mark.integration
def test_penalty_for_assignment_to_eligible_non_home_station() -> None:
    memberships = (
        _membership(HOME_STATION, is_home=True, is_replacement=False),
        _membership(OTHER_STATION, is_home=False, is_replacement=True),
    )

    assert (
        _penalty_for(
            memberships=memberships,
            worked_assignments={(OTHER_STATION.planning_unit_id, date(2024, 11, 1))},
        )
        == 1
    )


@pytest.mark.integration
def test_active_home_station_is_selected_per_assignment_date() -> None:
    memberships = (
        _membership(
            HOME_STATION,
            valid_until=date(2024, 11, 15),
            is_home=True,
            is_replacement=False,
        ),
        _membership(
            HOME_STATION,
            valid_from=date(2024, 11, 16),
            is_home=False,
            is_replacement=True,
        ),
        _membership(
            OTHER_STATION,
            valid_until=date(2024, 11, 15),
            is_home=False,
            is_replacement=True,
        ),
        _membership(
            OTHER_STATION,
            valid_from=date(2024, 11, 16),
            is_home=True,
            is_replacement=False,
        ),
    )
    worked_assignments = {
        (HOME_STATION.planning_unit_id, date(2024, 11, 14)),
        (OTHER_STATION.planning_unit_id, date(2024, 11, 14)),
        (HOME_STATION.planning_unit_id, date(2024, 11, 17)),
        (OTHER_STATION.planning_unit_id, date(2024, 11, 17)),
    }

    assert _penalty_for(memberships=memberships, worked_assignments=worked_assignments) == 2


@pytest.mark.integration
def test_shared_pool_home_employee_has_no_cross_station_penalty() -> None:
    memberships = (
        _membership(SHARED_POOL, is_home=True, is_replacement=False),
        _membership(HOME_STATION, is_home=False, is_replacement=True),
        _membership(OTHER_STATION, is_home=False, is_replacement=True),
    )
    worked_assignments = {
        (HOME_STATION.planning_unit_id, date(2024, 11, 1)),
        (OTHER_STATION.planning_unit_id, date(2024, 11, 2)),
    }

    assert _penalty_for(memberships=memberships, worked_assignments=worked_assignments) == 0
