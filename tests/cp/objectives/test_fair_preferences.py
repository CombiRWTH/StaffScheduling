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
    Wish,
    WishType,
)
from scheduling.solver.cp_sat.context import create_context
from scheduling.solver.cp_sat.objectives.fair_preferences import FairPreferencesObjective
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


def _penalty_for(wishes: tuple[Wish, ...], worked_assignments: set[tuple[date, int]]) -> float:
    dataset = SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(EARLY_SHIFT, LATE_SHIFT),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
        wishes=wishes,
    )
    ctx = create_context(dataset=dataset)
    create_assignment_variables(ctx)

    for (_employee_id, _unit, assignment_date, shift_id, _level), variable in ctx.assignment_variables.items():
        ctx.model.add(variable == ((assignment_date, shift_id) in worked_assignments))

    penalties = FairPreferencesObjective().add_to_model(ctx, params={})
    if not penalties:
        return 0

    ctx.model.minimize(sum(penalty.expression for penalty in penalties))
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return solver.objective_value


@pytest.mark.integration
def test_free_day_wish_counts_as_three_strikes_and_free_shift_as_one() -> None:
    wish_date = date(2024, 11, 4)
    free_day = Wish(
        employee_id=EMPLOYEE.employee_id,
        planning_unit_id=PLANNING_UNIT.planning_unit_id,
        date=wish_date,
        type=WishType.FREE_DAY,
    )
    free_shift = Wish(
        employee_id=EMPLOYEE.employee_id,
        planning_unit_id=PLANNING_UNIT.planning_unit_id,
        date=wish_date,
        type=WishType.FREE_SHIFT,
        shift_id=EARLY_SHIFT.shift_id,
    )

    assert _penalty_for((free_shift,), {(wish_date, EARLY_SHIFT.shift_id)}) == 1
    assert _penalty_for((free_day,), {(wish_date, LATE_SHIFT.shift_id)}) == 36
    assert _penalty_for((free_day, free_shift), {(wish_date, EARLY_SHIFT.shift_id)}) == 100


@pytest.mark.integration
def test_fulfilled_free_wishes_and_preferred_work_wishes_have_no_penalty() -> None:
    wish_date = date(2024, 11, 4)
    wishes = (
        Wish(
            employee_id=EMPLOYEE.employee_id,
            planning_unit_id=PLANNING_UNIT.planning_unit_id,
            date=wish_date,
            type=WishType.FREE_SHIFT,
            shift_id=EARLY_SHIFT.shift_id,
        ),
        Wish(
            employee_id=EMPLOYEE.employee_id,
            planning_unit_id=PLANNING_UNIT.planning_unit_id,
            date=wish_date,
            type=WishType.PREFERRED_DAY,
        ),
    )

    assert _penalty_for(wishes, {(wish_date, LATE_SHIFT.shift_id)}) == 0


@pytest.mark.integration
def test_preferred_day_counts_as_three_strikes_and_preferred_shift_as_one() -> None:
    wish_date = date(2024, 11, 4)
    preferred_day = Wish(
        employee_id=EMPLOYEE.employee_id,
        planning_unit_id=PLANNING_UNIT.planning_unit_id,
        date=wish_date,
        type=WishType.PREFERRED_DAY,
    )
    preferred_shift = Wish(
        employee_id=EMPLOYEE.employee_id,
        planning_unit_id=PLANNING_UNIT.planning_unit_id,
        date=wish_date,
        type=WishType.PREFERRED_SHIFT,
        shift_id=EARLY_SHIFT.shift_id,
    )

    assert _penalty_for((preferred_shift,), {(wish_date, LATE_SHIFT.shift_id)}) == 1
    assert _penalty_for((preferred_day,), set()) == 36


@pytest.mark.integration
def test_free_and_preferred_wishes_use_separate_strike_buckets() -> None:
    wish_date = date(2024, 11, 4)
    wishes = (
        Wish(
            employee_id=EMPLOYEE.employee_id,
            planning_unit_id=PLANNING_UNIT.planning_unit_id,
            date=wish_date,
            type=WishType.FREE_SHIFT,
            shift_id=EARLY_SHIFT.shift_id,
        ),
        Wish(
            employee_id=EMPLOYEE.employee_id,
            planning_unit_id=PLANNING_UNIT.planning_unit_id,
            date=wish_date,
            type=WishType.PREFERRED_SHIFT,
            shift_id=LATE_SHIFT.shift_id,
        ),
    )

    assert _penalty_for(wishes, {(wish_date, EARLY_SHIFT.shift_id)}) == 2
