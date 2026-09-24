import datetime
from unittest.mock import patch

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
from scheduling.solver.cp_sat.constraints.hierarchy_of_intermediate_shifts import HierarchyOfIntermediateShifts
from scheduling.solver.cp_sat.context import create_context

# --- Shared Test Entities ---

PLANNING_UNIT = PlanningUnit(
    planning_unit_id=1,
    display_name="Station 1",
    type=PlanningUnitType.STATION,
)

INTERMEDIATE_TEST_SHIFT = Shift(
    shift_id=1,
    code="Z",
    type=ShiftType.EARLY,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=540,
    end_minute=1020,
    net_work_minutes=450,
)

EMPLOYEE_1 = Employee(employee_id=1, display_name="Alice", staff_level=StaffLevel.PROFESSIONAL)
EMPLOYEE_2 = Employee(employee_id=2, display_name="Bob", staff_level=StaffLevel.PROFESSIONAL)

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


def _solve_with_setup(daily_shift_counts: dict[datetime.date, int]) -> cp_model.CpSolverStatus:
    """
    Erstellt eine isolierte Variablen-Matrix für die ISO-Woche 45 (04.11.24 - 10.11.24)
    und forciert exakt so viele Schichten pro Tag, wie in `daily_shift_counts` definiert.
    Restliche Variablen werden hart auf 0 gesetzt.
    """
    dataset = SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(INTERMEDIATE_TEST_SHIFT,),
        employees=(EMPLOYEE_1, EMPLOYEE_2),
        planning_unit_memberships=(MEMBERSHIP_1, MEMBERSHIP_2),
    )

    ctx = create_context(dataset=dataset)
    test_dates = [datetime.date(2024, 11, day) for day in range(4, 11)]

    for d in test_dates:
        for emp in [EMPLOYEE_1, EMPLOYEE_2]:
            key = (
                emp.employee_id,
                PLANNING_UNIT.planning_unit_id,
                d,
                INTERMEDIATE_TEST_SHIFT.shift_id,
                StaffLevel.PROFESSIONAL,
            )
            ctx.assignment_variables[key] = ctx.model.new_bool_var(f"assign_{emp.employee_id}_{d:%Y%m%d}")

    for d in test_dates:
        target_count = daily_shift_counts.get(d, 0)
        keys_for_day = [
            (
                emp.employee_id,
                PLANNING_UNIT.planning_unit_id,
                d,
                INTERMEDIATE_TEST_SHIFT.shift_id,
                StaffLevel.PROFESSIONAL,
            )
            for emp in [EMPLOYEE_1, EMPLOYEE_2]
        ]

        for i, key in enumerate(keys_for_day):
            if i < target_count:
                ctx.model.add(ctx.assignment_variables[key] == 1)
            else:
                ctx.model.add(ctx.assignment_variables[key] == 0)

    mock_target = "scheduling.solver.cp_sat.constraints.hierarchy_of_intermediate_shifts.is_intermediate_shift"
    with patch(mock_target, return_value=True):
        HierarchyOfIntermediateShifts().add_to_model(ctx, params={})

    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


# --- Test Cases ---


@pytest.mark.integration
def test_feasible_weekdays_level_one() -> None:
    counts = {datetime.date(2024, 11, 4 + i): (1 if i < 5 else 0) for i in range(7)}
    assert _solve_with_setup(counts) in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_weekend_without_weekdays() -> None:
    counts = {datetime.date(2024, 11, 4 + i): 1 for i in range(7)}
    counts[datetime.date(2024, 11, 8)] = 0
    counts[datetime.date(2024, 11, 10)] = 0

    assert _solve_with_setup(counts) == cp_model.INFEASIBLE


@pytest.mark.integration
def test_infeasible_uneven_weekdays() -> None:
    counts = {datetime.date(2024, 11, 4 + i): 0 for i in range(7)}
    counts[datetime.date(2024, 11, 4)] = 2

    assert _solve_with_setup(counts) == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_weekend_overflow() -> None:
    counts = {datetime.date(2024, 11, 4 + i): (2 if i < 5 else 1) for i in range(7)}

    assert _solve_with_setup(counts) in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_weekday_surpasses_weekend_by_two() -> None:
    counts = {datetime.date(2024, 11, 4 + i): (2 if i < 5 else 0) for i in range(7)}

    assert _solve_with_setup(counts) == cp_model.INFEASIBLE
