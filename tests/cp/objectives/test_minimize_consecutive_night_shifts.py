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
from scheduling.solver.cp_sat.objectives.minimize_consecutive_night_shifts import MinimizeConsecutiveNightShifts
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
def test_penalty_for_three_consecutive_night_shifts() -> None:
    # 3 consecutive nights → penalty expected
    dataset = _dataset()
    ctx = create_context(dataset=dataset)
    create_assignment_variables(ctx)

    night_dates = {date(2024, 11, 1), date(2024, 11, 2), date(2024, 11, 3)}
    for (_employee_id, _unit, d, shift_id, _level), var in ctx.assignment_variables.items():
        if d in night_dates and shift_id == NIGHT_SHIFT.shift_id:
            ctx.model.add(var == 1)
        else:
            ctx.model.add(var == 0)

    penalties = MinimizeConsecutiveNightShifts().add_to_model(ctx, params={})
    assert penalties

    total = sum(p.multiplier * p.expression for p in penalties)
    ctx.model.minimize(total)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    assert solver.objective_value > 0


@pytest.mark.integration
def test_no_penalty_for_single_night_shift() -> None:
    # Only 1 night shift → no consecutive phase → no penalty
    dataset = _dataset()
    ctx = create_context(dataset=dataset)
    create_assignment_variables(ctx)

    for (_employee_id, _unit, d, shift_id, _level), var in ctx.assignment_variables.items():
        if d == date(2024, 11, 1) and shift_id == NIGHT_SHIFT.shift_id:
            ctx.model.add(var == 1)
        else:
            ctx.model.add(var == 0)

    penalties = MinimizeConsecutiveNightShifts().add_to_model(ctx, params={})
    assert penalties

    total = sum(p.multiplier * p.expression for p in penalties)
    ctx.model.minimize(total)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    assert solver.objective_value == 0


@pytest.mark.integration
def test_longer_phase_has_higher_penalty() -> None:
    # 4 consecutive nights should produce a higher penalty than 2 consecutive nights
    def _penalty_for_nights(night_dates: set[date]) -> float:
        dataset = _dataset()
        ctx = create_context(dataset=dataset)
        create_assignment_variables(ctx)

        for (_employee_id, _unit, d, shift_id, _level), var in ctx.assignment_variables.items():
            if d in night_dates and shift_id == NIGHT_SHIFT.shift_id:
                ctx.model.add(var == 1)
            else:
                ctx.model.add(var == 0)

        penalties = MinimizeConsecutiveNightShifts().add_to_model(ctx, params={})
        total = sum(p.multiplier * p.expression for p in penalties)
        ctx.model.minimize(total)
        solver = cp_model.CpSolver()
        solver.solve(ctx.model)
        return solver.objective_value

    penalty_2 = _penalty_for_nights({date(2024, 11, 1), date(2024, 11, 2)})
    penalty_4 = _penalty_for_nights({date(2024, 11, 1), date(2024, 11, 2), date(2024, 11, 3), date(2024, 11, 4)})

    assert penalty_4 > penalty_2