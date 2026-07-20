from datetime import date

import pytest
from ortools.sat.python import cp_model

from scheduling.domain import (
    Employee,
    MonthlyWorkAccount,
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
from scheduling.solver.cp_sat.objectives.minimize_overtime import MinimizeOvertime
from scheduling.solver.cp_sat.variables import create_assignment_variables

PLANNING_UNIT = PlanningUnit(
    planning_unit_id=1,
    display_name="Station 1",
    type=PlanningUnitType.STATION,
)

ONE_HOUR_SHIFT = Shift(
    shift_id=1,
    code="F",
    type=ShiftType.EARLY,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=360,
    end_minute=420,
    net_work_minutes=60,
)

ALICE = Employee(
    employee_id=1,
    display_name="Alice",
    staff_level=StaffLevel.PROFESSIONAL,
)

BOB = Employee(
    employee_id=2,
    display_name="Bob",
    staff_level=StaffLevel.PROFESSIONAL,
)


def _membership_for(employee: Employee) -> PlanningUnitMembership:
    return PlanningUnitMembership(
        planning_unit_id=PLANNING_UNIT.planning_unit_id,
        employee_id=employee.employee_id,
        valid_from=date(2024, 11, 1),
        valid_until=date(2024, 11, 30),
        staff_level=StaffLevel.PROFESSIONAL,
        is_home=True,
        is_replacement=False,
    )


def _dataset(
    *,
    employees: tuple[Employee, ...] = (ALICE,),
    accounts: tuple[MonthlyWorkAccount, ...] = (),
) -> SchedulingDataset:
    return SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(ONE_HOUR_SHIFT,),
        employees=employees,
        planning_unit_memberships=tuple(_membership_for(employee) for employee in employees),
        monthly_work_accounts=accounts,
    )


def _penalty_for(
    *,
    accounts: tuple[MonthlyWorkAccount, ...],
    generated_shift_counts: dict[int, int],
) -> float:
    employees = tuple(employee for employee in (ALICE, BOB) if employee.employee_id in generated_shift_counts)
    ctx = create_context(dataset=_dataset(employees=employees, accounts=accounts))
    create_assignment_variables(ctx)

    for (employee_id, _unit, assignment_date, _shift, _level), variable in ctx.assignment_variables.items():
        ctx.model.add(variable == (assignment_date.day <= generated_shift_counts[employee_id]))

    penalties = MinimizeOvertime().add_to_model(ctx, params={})
    assert len(penalties) == 1

    penalty = penalties[0]
    assert penalty.objective_id == "minimize_overtime"
    assert penalty.name == "total_overtime"
    assert penalty.multiplier == 1

    ctx.model.minimize(penalty.multiplier * penalty.expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return solver.objective_value


def test_returns_no_penalties_without_assignment_variables() -> None:
    ctx = create_context(dataset=_dataset())

    assert MinimizeOvertime().add_to_model(ctx, params={}) == ()


@pytest.mark.integration
@pytest.mark.parametrize("generated_shift_count", [1, 2])
def test_no_penalty_at_or_below_remaining_target(generated_shift_count: int) -> None:
    account = MonthlyWorkAccount(employee_id=ALICE.employee_id, target_minutes=120)

    assert (
        _penalty_for(
            accounts=(account,),
            generated_shift_counts={ALICE.employee_id: generated_shift_count},
        )
        == 0
    )


@pytest.mark.integration
def test_penalty_equals_minutes_generated_above_remaining_target() -> None:
    account = MonthlyWorkAccount(employee_id=ALICE.employee_id, target_minutes=120)

    assert _penalty_for(accounts=(account,), generated_shift_counts={ALICE.employee_id: 3}) == 60


@pytest.mark.integration
def test_actual_minutes_reduce_remaining_target() -> None:
    account = MonthlyWorkAccount(
        employee_id=ALICE.employee_id,
        target_minutes=120,
        actual_minutes=60,
    )

    assert _penalty_for(accounts=(account,), generated_shift_counts={ALICE.employee_id: 2}) == 60


@pytest.mark.integration
def test_penalties_are_summed_across_employees() -> None:
    accounts = (
        MonthlyWorkAccount(employee_id=ALICE.employee_id, target_minutes=120),
        MonthlyWorkAccount(employee_id=BOB.employee_id, target_minutes=180, actual_minutes=60),
    )

    assert (
        _penalty_for(
            accounts=accounts,
            generated_shift_counts={ALICE.employee_id: 3, BOB.employee_id: 3},
        )
        == 120
    )
