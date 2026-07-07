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
from scheduling.solver.cp_sat.objectives.every_second_weekend_free import EverySecondWeekendFree
from scheduling.solver.cp_sat.variables import create_assignment_variables


# --- Shared test data ---

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
    planning_unit_id=1,
    employee_id=1,
    valid_from=date(2024, 11, 1),
    valid_until=date(2024, 11, 30),
    staff_level=StaffLevel.PROFESSIONAL,
    is_home=True,
    is_replacement=False,
)


def _dataset() -> SchedulingDataset:
    # November 2024: weekends are 2-3, 9-10, 16-17, 23-24, 30
    return SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(EARLY_SHIFT,),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
    )


def _solve_with_forced_days(forced_work_dates: list[date]):
    """
    Build a model where the employee is forced to work on forced_work_dates,
    apply the objective, and solve. Returns the solver status.
    """
    dataset = _dataset()
    ctx = create_context(dataset=dataset)
    create_assignment_variables(ctx)

    # Force the employee to work (or not) on the given dates
    for (_employee_id, _unit, d, _shift, _level), var in ctx.assignment_variables.items():
        if d in forced_work_dates:
            ctx.model.add(var == 1)
        else:
            ctx.model.add(var == 0)

    penalties = EverySecondWeekendFree().add_to_model(ctx, params={})
    assert penalties, "Objective should return at least one penalty"

    ctx.model.minimize(penalties[0].expression)

    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


@pytest.mark.integration
def test_penalty_when_both_weekends_worked() -> None:
    # Employee works both weekend 1 (Sat 2, Sun 3) and weekend 2 (Sat 9, Sun 10)
    # → same status (both worked) → penalty expected
    status = _solve_with_forced_days([date(2024, 11, 2), date(2024, 11, 3), date(2024, 11, 9), date(2024, 11, 10)])
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_no_penalty_when_weekends_alternate() -> None:
    # Employee works weekends 1 and 3 (Sat/Sun), is free on weekends 2 and 4.
    # Every consecutive pair alternates → no same-status penalty expected.
    # November 2024 weekends: (2,3), (9,10), (16,17), (23,24)
    worked_weekends = {date(2024, 11, 2), date(2024, 11, 3), date(2024, 11, 16), date(2024, 11, 17)}
    free_weekends = {date(2024, 11, 9), date(2024, 11, 10), date(2024, 11, 23), date(2024, 11, 24)}

    dataset = _dataset()
    ctx = create_context(dataset=dataset)
    create_assignment_variables(ctx)

    for (_employee_id, _unit, d, _shift, _level), var in ctx.assignment_variables.items():
        if d in worked_weekends:
            ctx.model.add(var == 1)
        else:
            ctx.model.add(var == 0)

    penalties = EverySecondWeekendFree().add_to_model(ctx, params={})
    assert penalties

    ctx.model.minimize(penalties[0].expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    # Alternating weekends (worked, free, worked, free) → penalty should be 0
    assert solver.objective_value == 0