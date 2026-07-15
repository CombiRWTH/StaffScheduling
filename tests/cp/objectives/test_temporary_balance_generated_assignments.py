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
from scheduling.solver.cp_sat.objectives.temporary_balance_generated_assignments import (
    TemporaryBalanceGeneratedAssignments,
)
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

MEMBERSHIPS = tuple(
    PlanningUnitMembership(
        planning_unit_id=PLANNING_UNIT.planning_unit_id,
        employee_id=employee.employee_id,
        valid_from=date(2024, 11, 1),
        valid_until=date(2024, 11, 30),
        staff_level=StaffLevel.PROFESSIONAL,
        is_home=True,
        is_replacement=False,
    )
    for employee in (ALICE, BOB)
)


def _dataset(*, employees: tuple[Employee, ...] = (ALICE, BOB)) -> SchedulingDataset:
    employee_ids = {employee.employee_id for employee in employees}

    return SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(EARLY_SHIFT,),
        employees=employees,
        planning_unit_memberships=tuple(
            membership for membership in MEMBERSHIPS if membership.employee_id in employee_ids
        ),
    )


def _penalty_for_counts(counts_by_employee: dict[int, int]) -> float:
    employees = tuple(employee for employee in (ALICE, BOB) if employee.employee_id in counts_by_employee)
    ctx = create_context(dataset=_dataset(employees=employees))
    create_assignment_variables(ctx)

    for (employee_id, _unit, assignment_date, _shift, _level), variable in ctx.assignment_variables.items():
        ctx.model.add(variable == (assignment_date.day <= counts_by_employee[employee_id]))

    penalties = TemporaryBalanceGeneratedAssignments().add_to_model(ctx, params={})
    assert len(penalties) == 1

    penalty = penalties[0]
    assert penalty.objective_id == "temporary_balance_generated_assignments"
    assert penalty.name == "max_generated_assignments_per_employee"
    assert penalty.multiplier == 1

    ctx.model.minimize(penalty.multiplier * penalty.expression)
    solver = cp_model.CpSolver()
    status = solver.solve(ctx.model)

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    return solver.objective_value


def test_returns_no_penalties_without_assignment_variables() -> None:
    ctx = create_context(dataset=_dataset())

    assert TemporaryBalanceGeneratedAssignments().add_to_model(ctx, params={}) == ()


@pytest.mark.integration
def test_penalty_equals_single_employee_assignment_count() -> None:
    assert _penalty_for_counts({ALICE.employee_id: 4}) == 4


@pytest.mark.integration
def test_penalty_equals_largest_employee_assignment_count() -> None:
    assert _penalty_for_counts({ALICE.employee_id: 3, BOB.employee_id: 7}) == 7


@pytest.mark.integration
def test_penalty_equals_common_count_when_employees_are_balanced() -> None:
    assert _penalty_for_counts({ALICE.employee_id: 5, BOB.employee_id: 5}) == 5
