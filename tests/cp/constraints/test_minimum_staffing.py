import datetime
from unittest.mock import PropertyMock, patch

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
from scheduling.solver.cp_sat.constraints.minimum_staffing import MinimumStaffing
from scheduling.solver.cp_sat.context import create_context

# --- Shared Test Entities ---

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
    end_minute=840,
    net_work_minutes=450,
)

EMPLOYEE_1 = Employee(
    employee_id=1,
    display_name="Alice",
    staff_level=StaffLevel.PROFESSIONAL,
)

EMPLOYEE_2 = Employee(
    employee_id=2,
    display_name="Bob",
    staff_level=StaffLevel.PROFESSIONAL,
)

MEMBERSHIP_1 = PlanningUnitMembership(
    planning_unit_id=1,
    employee_id=1,
    valid_from=datetime.date(2024, 11, 1),
    valid_until=datetime.date(2024, 11, 30),
    staff_level=StaffLevel.PROFESSIONAL,
    is_home=True,
    is_replacement=False,
)

MEMBERSHIP_2 = PlanningUnitMembership(
    planning_unit_id=1,
    employee_id=2,
    valid_from=datetime.date(2024, 11, 1),
    valid_until=datetime.date(2024, 11, 30),
    staff_level=StaffLevel.PROFESSIONAL,
    is_home=True,
    is_replacement=False,
)


def _solve_with_setup(required_count: int, assigned_employee_ids: list[int]) -> cp_model.CpSolverStatus:
    """
    Konstruiert das Modell für einen isolierten Tag, injiziert eine definierte Demand-Anforderung
    mittels Mocking in den Index und forciert Zuweisungen.
    """
    target_date = datetime.date(2024, 11, 5)

    dataset = SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(EARLY_SHIFT,),
        employees=(EMPLOYEE_1, EMPLOYEE_2),
        planning_unit_memberships=(MEMBERSHIP_1, MEMBERSHIP_2),
    )

    ctx = create_context(dataset=dataset)

    # 1. Isolation: Dichte Variablenmatrix für den Ziel-Tag aufbauen
    for emp in (EMPLOYEE_1, EMPLOYEE_2):
        key = (
            emp.employee_id,
            PLANNING_UNIT.planning_unit_id,
            target_date,
            EARLY_SHIFT.shift_id,
            StaffLevel.PROFESSIONAL,
        )
        ctx.assignment_variables[key] = ctx.model.new_bool_var(f"assign_{emp.employee_id}")

    # 2. Booleschen Zustandsraum deterministisch beschränken (1=Forciert, 0=Verboten)
    for emp in (EMPLOYEE_1, EMPLOYEE_2):
        key = (
            emp.employee_id,
            PLANNING_UNIT.planning_unit_id,
            target_date,
            EARLY_SHIFT.shift_id,
            StaffLevel.PROFESSIONAL,
        )
        if emp.employee_id in assigned_employee_ids:
            ctx.model.add(ctx.assignment_variables[key] == 1)
        else:
            ctx.model.add(ctx.assignment_variables[key] == 0)

    # 3. Constraint injizieren und schreibgeschützten Index mocken
    demand_key = (PLANNING_UNIT.planning_unit_id, target_date, EARLY_SHIFT.shift_id, StaffLevel.PROFESSIONAL)

    with patch.object(type(ctx.index), "required_count_by_demand_key", new_callable=PropertyMock) as mock_demand:
        mock_demand.return_value = {demand_key: required_count}
        MinimumStaffing().add_to_model(ctx, params={})

    # 4. Solver evaluieren
    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


# --- Test Cases ---


@pytest.mark.integration
def test_infeasible_when_understaffed() -> None:
    """Prüft, ob der Constraint anschlägt, wenn weniger Personal als benötigt zugeteilt ist."""
    status = _solve_with_setup(required_count=2, assigned_employee_ids=[1])
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_when_exactly_staffed() -> None:
    """Prüft, ob der Constraint exakte Bedarfsabdeckung zulässt."""
    status = _solve_with_setup(required_count=2, assigned_employee_ids=[1, 2])
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_feasible_when_overstaffed() -> None:
    """Prüft, ob der Constraint Überbesetzung zulässt."""
    status = _solve_with_setup(required_count=1, assigned_employee_ids=[1, 2])
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_when_no_staff_assigned() -> None:
    """Prüft die Verletzung, wenn der Bedarf > 0 ist, aber niemand arbeitet."""
    status = _solve_with_setup(required_count=1, assigned_employee_ids=[])
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_when_zero_demand_and_no_staff() -> None:
    """Prüft den Randfall: 0 Bedarf und 0 Personal ist zulässig."""
    status = _solve_with_setup(required_count=0, assigned_employee_ids=[])
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
