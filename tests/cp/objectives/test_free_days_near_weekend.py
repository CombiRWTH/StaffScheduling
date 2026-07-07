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
from scheduling.solver.cp_sat.objectives.free_days_near_weekend import FreeDaysNearWeekend
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
    planning_unit_id=1,
    employee_id=1,
    valid_from=date(2024, 11, 1),
    valid_until=date(2024, 11, 30),
    staff_level=StaffLevel.PROFESSIONAL,
    is_home=True,
    is_replacement=False,
)


def _dataset() -> SchedulingDataset:
    # November 2024: Mon 4, Fri 1, Sat 2 are useful test dates
    return SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(EARLY_SHIFT,),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
    )


@pytest.mark.integration
def test_higher_reward_when_friday_and_saturday_both_free() -> None:
    # Friday (Nov 1) and Saturday (Nov 2) both free → bigger reward than only Friday free
    dataset = _dataset()
    ctx_both = create_context(dataset=dataset)
    create_assignment_variables(ctx_both)

    for (_employee_id, _unit, d, _shift, _level), var in ctx_both.assignment_variables.items():
        ctx_both.model.add(var == 0)  # all days free

    penalties_both = FreeDaysNearWeekend().add_to_model(ctx_both, params={})
    assert penalties_both
    ctx_both.model.minimize(penalties_both[0].expression)  # multiplier=-1 so minimizing = maximizing reward
    solver_both = cp_model.CpSolver()
    solver_both.solve(ctx_both.model)
    reward_both = -solver_both.objective_value  # negate because multiplier=-1

    # Now force Friday worked → less reward
    dataset2 = _dataset()
    ctx_fri = create_context(dataset=dataset2)
    create_assignment_variables(ctx_fri)

    for (_employee_id, _unit, d, _shift, _level), var in ctx_fri.assignment_variables.items():
        if d == date(2024, 11, 1):
            ctx_fri.model.add(var == 1)  # Friday worked
        else:
            ctx_fri.model.add(var == 0)

    penalties_fri = FreeDaysNearWeekend().add_to_model(ctx_fri, params={})
    assert penalties_fri
    ctx_fri.model.minimize(penalties_fri[0].expression)
    solver_fri = cp_model.CpSolver()
    solver_fri.solve(ctx_fri.model)
    reward_fri = -solver_fri.objective_value

    # All free should give more reward than Friday worked.
    # Values are negative because multiplier=-1; less negative = higher reward.
    assert reward_both < reward_fri


@pytest.mark.integration
def test_no_reward_when_all_days_worked() -> None:
    # All days worked → no free near-weekend days → reward should be 0
    dataset = _dataset()
    ctx = create_context(dataset=dataset)
    create_assignment_variables(ctx)

    for (_employee_id, _unit, d, _shift, _level), var in ctx.assignment_variables.items():
        ctx.model.add(var == 1)  # all days worked

    penalties = FreeDaysNearWeekend().add_to_model(ctx, params={})
    assert penalties

    ctx.model.minimize(penalties[0].expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    # No free near-weekend days → reward = 0, so penalty expression = 0
    assert solver.objective_value == 0