import datetime

import pytest
from ortools.sat.python import cp_model

from scheduling.domain import (
    Capability,
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
from scheduling.solver.cp_sat.constraints.rounds_in_early_shift import RoundsInEarlyShift
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

EMPLOYEE_WITH_ROUNDS = Employee(
    employee_id=1,
    display_name="Alice",
    staff_level=StaffLevel.PROFESSIONAL,
    capabilities=(Capability.ROUNDS,),
)

EMPLOYEE_WITHOUT_ROUNDS = Employee(
    employee_id=2,
    display_name="Bob",
    staff_level=StaffLevel.PROFESSIONAL,
    capabilities=(),
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


def _solve_with_setup(
    target_date: datetime.date,
    forced_assignments: list[tuple[int, int]],
) -> cp_model.CpSolverStatus:
    """
    Konstruiert das Modell für einen isolierten Tag und forciert deterministisch Zuweisungen.
    Nutzt eine dichte Variablenmatrix, um die rein mathematische Logik des Constraints zu beweisen.
    """
    dataset = SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(EARLY_SHIFT, LATE_SHIFT),
        employees=(EMPLOYEE_WITH_ROUNDS, EMPLOYEE_WITHOUT_ROUNDS),
        planning_unit_memberships=(MEMBERSHIP_1, MEMBERSHIP_2),
    )

    ctx = create_context(dataset=dataset)

    # 1. Isolation: Dichte Variablenmatrix für den Ziel-Tag aufbauen
    for emp in (EMPLOYEE_WITH_ROUNDS, EMPLOYEE_WITHOUT_ROUNDS):
        for shift in (EARLY_SHIFT, LATE_SHIFT):
            key = (
                emp.employee_id,
                PLANNING_UNIT.planning_unit_id,
                target_date,
                shift.shift_id,
                StaffLevel.PROFESSIONAL,
            )
            ctx.assignment_variables[key] = ctx.model.new_bool_var(f"assign_{emp.employee_id}_{shift.shift_id}")

    # 2. Booleschen Zustandsraum deterministisch beschränken (1=Forciert, 0=Verboten)
    for emp in (EMPLOYEE_WITH_ROUNDS, EMPLOYEE_WITHOUT_ROUNDS):
        for shift in (EARLY_SHIFT, LATE_SHIFT):
            key = (
                emp.employee_id,
                PLANNING_UNIT.planning_unit_id,
                target_date,
                shift.shift_id,
                StaffLevel.PROFESSIONAL,
            )
            if (emp.employee_id, shift.shift_id) in forced_assignments:
                ctx.model.add(ctx.assignment_variables[key] == 1)
            else:
                ctx.model.add(ctx.assignment_variables[key] == 0)

    # 3. Constraint injizieren
    RoundsInEarlyShift().add_to_model(ctx, params={})

    # 4. Solver evaluieren
    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


# --- Test Cases ---


@pytest.mark.integration
def test_feasible_weekday_when_qualified_employee_in_early_shift() -> None:
    """Beweist die Zulässigkeit, wenn eine qualifizierte Person an einem Wochentag die Frühschicht besetzt."""
    weekday = datetime.date(2024, 11, 5)  # Dienstag
    status = _solve_with_setup(
        target_date=weekday, forced_assignments=[(EMPLOYEE_WITH_ROUNDS.employee_id, EARLY_SHIFT.shift_id)]
    )
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_weekday_when_no_qualified_employee_in_early_shift() -> None:
    """Beweist die Verletzung, wenn an einem Wochentag in der Frühschicht die Visiten-Qualifikation fehlt."""
    weekday = datetime.date(2024, 11, 5)  # Dienstag
    status = _solve_with_setup(
        target_date=weekday, forced_assignments=[(EMPLOYEE_WITHOUT_ROUNDS.employee_id, EARLY_SHIFT.shift_id)]
    )
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_infeasible_weekday_when_qualified_employee_in_late_shift() -> None:
    """Beweist, dass die Qualifikation explizit in der Frühschicht (nicht Spät) vorliegen muss."""
    weekday = datetime.date(2024, 11, 5)  # Dienstag
    status = _solve_with_setup(
        target_date=weekday,
        forced_assignments=[
            (EMPLOYEE_WITHOUT_ROUNDS.employee_id, EARLY_SHIFT.shift_id),
            (EMPLOYEE_WITH_ROUNDS.employee_id, LATE_SHIFT.shift_id),
        ],
    )
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_weekend_when_no_qualified_employee_assigned() -> None:
    """Beweist die topologische Ausnahme: Wochenenden erfordern keine Visiten-Qualifikation."""
    weekend = datetime.date(2024, 11, 9)  # Samstag
    status = _solve_with_setup(
        target_date=weekend, forced_assignments=[(EMPLOYEE_WITHOUT_ROUNDS.employee_id, EARLY_SHIFT.shift_id)]
    )
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
