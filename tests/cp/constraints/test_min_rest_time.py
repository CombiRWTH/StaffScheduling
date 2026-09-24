import datetime

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
from scheduling.solver.cp_sat.constraints.min_rest_time import MinimumRestTime
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
    start_minute=360,  # 06:00
    end_minute=840,  # 14:00
    net_work_minutes=450,
)

LATE_SHIFT = Shift(
    shift_id=2,
    code="S",
    type=ShiftType.LATE,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=810,  # 13:30
    end_minute=1290,  # 21:30
    net_work_minutes=450,
)

EMPLOYEE = Employee(
    employee_id=1,
    display_name="Alice",
    staff_level=StaffLevel.PROFESSIONAL,
)

MEMBERSHIP = PlanningUnitMembership(
    planning_unit_id=1,
    employee_id=1,
    valid_from=datetime.date(2024, 11, 1),
    valid_until=datetime.date(2024, 11, 30),
    staff_level=StaffLevel.PROFESSIONAL,
    is_home=True,
    is_replacement=False,
)


def _solve_with_setup(forced_assignments: list[tuple[datetime.date, int]]) -> cp_model.CpSolverStatus:
    """
    Konstruiert das Modell über einen isolierten Zeitraum und evaluiert die Zulässigkeit
    spezifischer Schichtübergänge. Iteriert als 'Dense Matrix', um Pruning-Effekte auszuschließen.
    """
    dataset = SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(EARLY_SHIFT, LATE_SHIFT),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
    )

    ctx = create_context(dataset=dataset)
    test_dates = [datetime.date(2024, 11, day) for day in range(1, 10)]

    # 1. Isolation: Dichte Variablenmatrix aufbauen
    for d in test_dates:
        for shift in (EARLY_SHIFT, LATE_SHIFT):
            key = (EMPLOYEE.employee_id, PLANNING_UNIT.planning_unit_id, d, shift.shift_id, StaffLevel.PROFESSIONAL)
            ctx.assignment_variables[key] = ctx.model.new_bool_var(f"assign_{d:%Y%m%d}_{shift.shift_id}")

    # 2. Booleschen Zustandsraum deterministisch beschränken (1=Forciert, 0=Verboten)
    for d in test_dates:
        for shift in (EARLY_SHIFT, LATE_SHIFT):
            key = (EMPLOYEE.employee_id, PLANNING_UNIT.planning_unit_id, d, shift.shift_id, StaffLevel.PROFESSIONAL)
            if (d, shift.shift_id) in forced_assignments:
                ctx.model.add(ctx.assignment_variables[key] == 1)
            else:
                ctx.model.add(ctx.assignment_variables[key] == 0)

    # 3. Constraint injizieren
    MinimumRestTime().add_to_model(ctx, params={})

    # 4. Solver evaluieren
    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


# --- Test Cases ---


@pytest.mark.integration
def test_infeasible_late_followed_by_early() -> None:
    """Prüft die Verletzung der minimalen Ruhezeit (Spätschicht -> Frühschicht am Folgetag)."""
    t_0 = datetime.date(2024, 11, 5)
    t_1 = datetime.date(2024, 11, 6)

    status = _solve_with_setup([(t_0, LATE_SHIFT.shift_id), (t_1, EARLY_SHIFT.shift_id)])

    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_early_followed_by_late() -> None:
    """Prüft die Zulässigkeit des inversen Übergangs (Frühschicht -> Spätschicht am Folgetag)."""
    t_0 = datetime.date(2024, 11, 5)
    t_1 = datetime.date(2024, 11, 6)

    status = _solve_with_setup([(t_0, EARLY_SHIFT.shift_id), (t_1, LATE_SHIFT.shift_id)])

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_feasible_late_followed_by_late() -> None:
    """Prüft die Zulässigkeit homogener Schichtblöcke (Spätschicht -> Spätschicht)."""
    t_0 = datetime.date(2024, 11, 5)
    t_1 = datetime.date(2024, 11, 6)

    status = _solve_with_setup([(t_0, LATE_SHIFT.shift_id), (t_1, LATE_SHIFT.shift_id)])

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_feasible_early_followed_by_early() -> None:
    """Prüft die Zulässigkeit homogener Schichtblöcke (Frühschicht -> Frühschicht)."""
    t_0 = datetime.date(2024, 11, 5)
    t_1 = datetime.date(2024, 11, 6)

    status = _solve_with_setup([(t_0, EARLY_SHIFT.shift_id), (t_1, EARLY_SHIFT.shift_id)])

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_feasible_late_followed_by_free_followed_by_early() -> None:
    """Prüft die topologische Unterbrechung durch einen freien Tag ($t+1$)."""
    t_0 = datetime.date(2024, 11, 5)
    t_2 = datetime.date(2024, 11, 7)  # Überspringt den 6. November

    status = _solve_with_setup([(t_0, LATE_SHIFT.shift_id), (t_2, EARLY_SHIFT.shift_id)])

    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
