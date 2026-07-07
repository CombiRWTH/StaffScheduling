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
from scheduling.solver.cp_sat.objectives.free_day_after_night_shift_phase import FreeDaysAfterNightShiftPhase
from scheduling.solver.cp_sat.variables import create_assignment_variables

PLANNING_UNIT = PlanningUnit(
    planning_unit_id=1,
    display_name="Station 1",
    type=PlanningUnitType.STATION,
)

NIGHT_SHIFT = Shift(
    shift_id=1,
    code="N",
    type=ShiftType.NIGHT,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=1320,
    end_minute=420,
    net_work_minutes=460,
)

EARLY_SHIFT = Shift(
    shift_id=2,
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
    return SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(NIGHT_SHIFT, EARLY_SHIFT),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
    )


@pytest.mark.integration
def test_penalty_when_working_on_day_after_next() -> None:
    # Pattern: night on day 1, free on day 2, working on day 3 → penalty
    dataset = _dataset()
    ctx = create_context(dataset=dataset)
    create_assignment_variables(ctx)

    for (_employee_id, _unit, d, shift_id, _level), var in ctx.assignment_variables.items():
        if d == date(2024, 11, 1) and shift_id == NIGHT_SHIFT.shift_id:
            ctx.model.add(var == 1)   # night shift on day 1
        elif d == date(2024, 11, 2):
            ctx.model.add(var == 0)   # free on day 2
        elif d == date(2024, 11, 3) and shift_id == EARLY_SHIFT.shift_id:
            ctx.model.add(var == 1)   # working on day 3
        else:
            ctx.model.add(var == 0)

    penalties = FreeDaysAfterNightShiftPhase().add_to_model(ctx, params={})
    assert penalties

    ctx.model.minimize(penalties[0].expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    # night → free → work pattern should produce a penalty
    assert solver.objective_value > 0


@pytest.mark.integration
def test_no_penalty_when_two_free_days_after_night() -> None:
    # Pattern: night on day 1, free on day 2, free on day 3 → no penalty
    dataset = _dataset()
    ctx = create_context(dataset=dataset)
    create_assignment_variables(ctx)

    for (_employee_id, _unit, d, shift_id, _level), var in ctx.assignment_variables.items():
        if d == date(2024, 11, 1) and shift_id == NIGHT_SHIFT.shift_id:
            ctx.model.add(var == 1)   # night shift on day 1
        else:
            ctx.model.add(var == 0)   # free on all other days

    penalties = FreeDaysAfterNightShiftPhase().add_to_model(ctx, params={})
    assert penalties

    ctx.model.minimize(penalties[0].expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    # two free days after night → no penalty
    assert solver.objective_value == 0