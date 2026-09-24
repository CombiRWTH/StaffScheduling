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
from scheduling.solver.cp_sat.constraints.one_assignment_per_day import OneAssignmentPerDay
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
LATE_SHIFT = Shift(
    shift_id=2,
    code="S",
    type=ShiftType.LATE,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=810,
    end_minute=1290,
    net_work_minutes=450,
)
NIGHT_SHIFT = Shift(
    shift_id=3,
    code="N",
    type=ShiftType.NIGHT,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=1200,
    end_minute=180,
    net_work_minutes=420,
)

SHIFTS = (EARLY_SHIFT, LATE_SHIFT, NIGHT_SHIFT)

EMPLOYEES = (
    Employee(employee_id=1, display_name="Alice", staff_level=StaffLevel.PROFESSIONAL),
    Employee(employee_id=2, display_name="Bob", staff_level=StaffLevel.PROFESSIONAL),
    Employee(employee_id=3, display_name="Charlie", staff_level=StaffLevel.PROFESSIONAL),
    Employee(employee_id=4, display_name="Diana", staff_level=StaffLevel.PROFESSIONAL),
)

MEMBERSHIPS = tuple(
    PlanningUnitMembership(
        planning_unit_id=1,
        employee_id=emp.employee_id,
        valid_from=datetime.date(2024, 11, 1),
        valid_until=datetime.date(2024, 11, 30),
        staff_level=StaffLevel.PROFESSIONAL,
        is_home=True,
        is_replacement=False,
    )
    for emp in EMPLOYEES
)


def _solve_with_setup(
    demands_by_shift_id: dict[int, int],
    available_employee_ids: list[int],
) -> cp_model.CpSolverStatus:
    """
    Konstruiert das Modell für 4 Mitarbeiter und 3 Schichten und evaluiert
    die kombinatorische Schnittmenge aus Bedarfsdeckung und der "Eine-Schicht-pro-Tag"-Restriktion.
    """
    target_date = datetime.date(2024, 11, 5)

    dataset = SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=SHIFTS,
        employees=EMPLOYEES,
        planning_unit_memberships=MEMBERSHIPS,
    )

    ctx = create_context(dataset=dataset)

    # 1. Isolation: Dichte Variablenmatrix (Dense Matrix: 4 Employees * 3 Shifts = 12 boolean vars)
    for emp in EMPLOYEES:
        for shift in SHIFTS:
            key = (
                emp.employee_id,
                PLANNING_UNIT.planning_unit_id,
                target_date,
                shift.shift_id,
                StaffLevel.PROFESSIONAL,
            )
            ctx.assignment_variables[key] = ctx.model.new_bool_var(f"assign_{emp.employee_id}_{shift.shift_id}")

    # 2. Hard-Constraints für Verfügbarkeit (Domänen-Reduktion)
    for emp in EMPLOYEES:
        if emp.employee_id not in available_employee_ids:
            for shift in SHIFTS:
                key = (
                    emp.employee_id,
                    PLANNING_UNIT.planning_unit_id,
                    target_date,
                    shift.shift_id,
                    StaffLevel.PROFESSIONAL,
                )
                ctx.model.add(ctx.assignment_variables[key] == 0)

    # 3. Dynamisches Mocking des Index-Lookups für den Bedarf
    injected_demand = {}
    for shift_id, required_count in demands_by_shift_id.items():
        demand_key = (PLANNING_UNIT.planning_unit_id, target_date, shift_id, StaffLevel.PROFESSIONAL)
        injected_demand[demand_key] = required_count

    with patch.object(type(ctx.index), "required_count_by_demand_key", new_callable=PropertyMock) as mock_demand:
        mock_demand.return_value = injected_demand

        # Constraints injizieren
        MinimumStaffing().add_to_model(ctx, params={})
        OneAssignmentPerDay().add_to_model(ctx, params={})

    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


# --- Test Cases ---


@pytest.mark.integration
def test_feasible_exact_global_match() -> None:
    """Zulässig: Exakte Zuweisung (1 Früh, 1 Spät, 2 Nacht) verteilt auf 4 verfügbare Mitarbeiter."""
    status = _solve_with_setup(
        demands_by_shift_id={EARLY_SHIFT.shift_id: 1, LATE_SHIFT.shift_id: 1, NIGHT_SHIFT.shift_id: 2},
        available_employee_ids=[1, 2, 3, 4],
    )
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_global_pigeonhole() -> None:
    """Unzulässig (Schubfachprinzip): Der kumulierte
    Tagesbedarf (5) übersteigt die verfügbaren Mitarbeiter (4)."""
    status = _solve_with_setup(
        demands_by_shift_id={EARLY_SHIFT.shift_id: 2, LATE_SHIFT.shift_id: 2, NIGHT_SHIFT.shift_id: 1},
        available_employee_ids=[1, 2, 3, 4],
    )
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_infeasible_local_shift_overdemand() -> None:
    """Unzulässig: Ausreichend Gesamtpersonal (4),
    aber eine einzelne Schicht fordert mehr Personal (5)."""
    status = _solve_with_setup(
        demands_by_shift_id={EARLY_SHIFT.shift_id: 5, LATE_SHIFT.shift_id: 0, NIGHT_SHIFT.shift_id: 0},
        available_employee_ids=[1, 2, 3, 4],
    )
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_heavy_clustering_on_one_shift() -> None:
    """Zulässig: Der gesamte verfügbare Pool (4) wird in eine einzige Schicht geclustert."""
    status = _solve_with_setup(
        demands_by_shift_id={EARLY_SHIFT.shift_id: 0, LATE_SHIFT.shift_id: 4, NIGHT_SHIFT.shift_id: 0},
        available_employee_ids=[1, 2, 3, 4],
    )
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_incremental_starvation() -> None:
    """Unzulässig: Geringer Bedarf pro Schicht (jeweils 1),
    aber in Summe (3) fehlt ein Mitarbeiter (nur 2 verfügbar)."""
    status = _solve_with_setup(
        demands_by_shift_id={EARLY_SHIFT.shift_id: 1, LATE_SHIFT.shift_id: 1, NIGHT_SHIFT.shift_id: 1},
        available_employee_ids=[1, 2],  # Nur Alice und Bob
    )
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_asymmetric_overstaffing_potential() -> None:
    """Zulässig: Geringer Bedarf (1), aber maximaler Pool (4). Beweist, dass MinimumStaffing (>=)
    nicht künstlich nach oben limitiert, solange OneAssignmentPerDay (<=1) eingehalten wird."""
    status = _solve_with_setup(demands_by_shift_id={EARLY_SHIFT.shift_id: 1}, available_employee_ids=[1, 2, 3, 4])
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_feasible_zero_demand_full_availability() -> None:
    """Zulässig (Leermenge): Keine Anforderungen, voller Pool. Solver weist allen 0 Schichten zu."""
    status = _solve_with_setup(demands_by_shift_id={}, available_employee_ids=[1, 2, 3, 4])
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_feasible_zero_demand_zero_availability() -> None:
    """Zulässig (Vakuum): Weder Bedarf noch Personal vorhanden."""
    status = _solve_with_setup(demands_by_shift_id={}, available_employee_ids=[])
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_minimal_gap() -> None:
    """Unzulässig: Bedarf exakt 1 höher (3) als verfügbares Personal (2), verteilt auf 2 Schichten."""
    status = _solve_with_setup(
        demands_by_shift_id={EARLY_SHIFT.shift_id: 2, LATE_SHIFT.shift_id: 1}, available_employee_ids=[1, 2]
    )
    assert status == cp_model.INFEASIBLE
