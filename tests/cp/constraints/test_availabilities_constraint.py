import datetime

import pytest
from ortools.sat.python import cp_model

from scheduling.domain import (
    Availability,
    AvailabilityType,
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
from scheduling.solver.cp_sat.constraints.availabilities_constraint import AvailabilitiesConstraint
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
    end_minute=820,
    net_work_minutes=460,
)

NIGHT_SHIFT = Shift(
    shift_id=2,
    code="N",
    type=ShiftType.NIGHT,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=1200,
    end_minute=180,  # 03:00 (crosses midnight)
    net_work_minutes=420,
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


def _solve_with_setup(
    availabilities: list[Availability],
    forced_assignments: list[tuple[datetime.date, int]],
) -> cp_model.CpSolverStatus:
    dataset = SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(EARLY_SHIFT, NIGHT_SHIFT),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
        availability=tuple(availabilities),
    )

    ctx = create_context(dataset=dataset)

    # 1. ISOLATION: Wir umgehen create_assignment_variables() und bauen
    # stattdessen manuell eine vollständige (dense) Variablen-Matrix auf.
    for day in range(1, 31):
        d = datetime.date(2024, 11, day)
        for shift in (EARLY_SHIFT, NIGHT_SHIFT):
            # Der Key entspricht Ihrem System: (emp_id, unit_id, date, shift_id, staff_level)
            key = (1, 1, d, shift.shift_id, StaffLevel.PROFESSIONAL)
            var = ctx.model.new_bool_var(f"assign_{d:%Y%m%d}_{shift.shift_id}")
            ctx.assignment_variables[key] = var

    # 2. Erzwingen der Test-Bedingungen (wir setzen die Ziel-Variablen auf 1)
    for target_date, shift_id in forced_assignments:
        key = (1, 1, target_date, shift_id, StaffLevel.PROFESSIONAL)
        ctx.model.add(ctx.assignment_variables[key] == 1)

    # 3. Constraint anwenden (jetzt muss ER beweisen, dass er blockierte Schichten auf 0 zwingt)
    AvailabilitiesConstraint().add_to_model(ctx, params={})

    # 4. Solver starten
    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


# --- Test Cases ---


@pytest.mark.integration
def test_infeasible_when_assigned_on_fully_blocked_day() -> None:
    target_date = datetime.date(2024, 11, 5)
    availabilities = [
        Availability(
            employee_id=1,
            date=target_date,
            availability_type=AvailabilityType.UNAVAILABLE,
        )
    ]

    status = _solve_with_setup(availabilities, [(target_date, EARLY_SHIFT.shift_id)])
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_infeasible_when_assigned_to_unallowed_shift() -> None:
    target_date = datetime.date(2024, 11, 5)
    availabilities = [
        Availability(
            employee_id=1,
            date=target_date,
            availability_type=AvailabilityType.AVAILABLE_ONLY,
            shift_ids=(EARLY_SHIFT.shift_id,),
        )
    ]

    status = _solve_with_setup(availabilities, [(target_date, NIGHT_SHIFT.shift_id)])
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_when_assigned_to_allowed_shift() -> None:
    target_date = datetime.date(2024, 11, 5)
    availabilities = [
        Availability(
            employee_id=1,
            date=target_date,
            availability_type=AvailabilityType.AVAILABLE_ONLY,
            shift_ids=(EARLY_SHIFT.shift_id,),
        )
    ]

    status = _solve_with_setup(availabilities, [(target_date, EARLY_SHIFT.shift_id)])
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_when_night_shift_spills_over_into_blocked_day() -> None:
    night_shift_date = datetime.date(2024, 11, 5)
    blocked_date = datetime.date(2024, 11, 6)

    availabilities = [
        Availability(
            employee_id=1,
            date=blocked_date,
            availability_type=AvailabilityType.UNAVAILABLE,
        )
    ]

    status = _solve_with_setup(availabilities, [(night_shift_date, NIGHT_SHIFT.shift_id)])
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_when_early_shift_precedes_blocked_day() -> None:
    early_shift_date = datetime.date(2024, 11, 5)
    blocked_date = datetime.date(2024, 11, 6)

    availabilities = [
        Availability(
            employee_id=1,
            date=blocked_date,
            availability_type=AvailabilityType.UNAVAILABLE,
        )
    ]

    status = _solve_with_setup(availabilities, [(early_shift_date, EARLY_SHIFT.shift_id)])
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
