import datetime
from unittest.mock import MagicMock, patch

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
from scheduling.solver.cp_sat.constraints.target_working_time import TargetWorkingTime
from scheduling.solver.cp_sat.context import create_context

# --- Shared Test Entities ---

PLANNING_UNIT = PlanningUnit(
    planning_unit_id=1,
    display_name="Station 1",
    type=PlanningUnitType.STATION,
)

# A standard 8-hour shift.
# Note: The constraint calculates duration algebraically as (end_minute - start_minute).
STANDARD_SHIFT = Shift(
    shift_id=1,
    code="D",
    type=ShiftType.EARLY,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=480,  # 08:00
    end_minute=960,  # 16:00
    net_work_minutes=480,
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
    target_minutes: int,
    actual_minutes: int,
    assigned_shift_count: int,
    tolerance_less: int = 120,
    tolerance_more: int = 120,
) -> cp_model.CpSolverStatus:
    """
    Constructs the model and evaluates the algebraic bounds of the TargetWorkingTime constraint.
    Iterates as a 'Dense Matrix' to prevent heuristic pruning from circumventing the mathematical proof.
    """
    account = MonthlyWorkAccount(
        employee_id=EMPLOYEE.employee_id,
        target_minutes=target_minutes,
        actual_minutes=actual_minutes,
    )

    dataset = SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=(STANDARD_SHIFT,),
        employees=(EMPLOYEE,),
        planning_unit_memberships=(MEMBERSHIP,),
        monthly_work_accounts=(account,),
    )

    ctx = create_context(dataset=dataset)
    test_dates = [datetime.date(2024, 11, day) for day in range(1, 6)]  # 5 potential assignment days

    # 1. Isolation: Generate a dense boolean variable matrix
    keys_in_order: list[tuple[int, int, datetime.date, int, StaffLevel]] = []
    for d in test_dates:
        key = (
            EMPLOYEE.employee_id,
            PLANNING_UNIT.planning_unit_id,
            d,
            STANDARD_SHIFT.shift_id,
            StaffLevel.PROFESSIONAL,
        )
        keys_in_order.append(key)
        ctx.assignment_variables[key] = ctx.model.new_bool_var(f"assign_{d:%Y%m%d}")

    # 2. Deterministically constrain the boolean state space
    for i, key in enumerate(keys_in_order):
        if i < assigned_shift_count:
            ctx.model.add(ctx.assignment_variables[key] == 1)
        else:
            ctx.model.add(ctx.assignment_variables[key] == 0)

    # 3. Inject Constraint & Mock TimeOffice Facts
    mock_facts = MagicMock()
    mock_facts.target_working_time_tolerance_less = tolerance_less
    mock_facts.target_working_time_tolerance_more = tolerance_more

    mock_target = "scheduling.solver.cp_sat.constraints.target_working_time.facts.TIMEOFFICE_FACTS"
    with patch(mock_target, mock_facts):
        TargetWorkingTime().add_to_model(ctx, params={})

    # 4. Evaluate Solver
    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


# --- Test Cases ---


@pytest.mark.integration
def test_feasible_exact_target_match() -> None:
    """Proves feasibility when the assigned sum perfectly matches the net target."""
    # Target: 960, Actual: 0 -> Net Target: 960 (Requires exactly 2 shifts of 480m)
    status = _solve_with_setup(target_minutes=960, actual_minutes=0, assigned_shift_count=2)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_infeasible_below_lower_tolerance() -> None:
    """Proves infeasibility when assignments fall below the strict lower boundary."""
    # Target: 960, Actual: 0, Assigned: 1 shift (480m). Boundary is [960 - 120, 960 + 120] = [840, 1080].
    # 480 < 840.
    status = _solve_with_setup(target_minutes=960, actual_minutes=0, assigned_shift_count=1)
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_infeasible_above_upper_tolerance() -> None:
    """Proves infeasibility when assignments exceed the strict upper boundary."""
    # Target: 960, Actual: 0, Assigned: 3 shifts (1440m). Boundary is [840, 1080].
    # 1440 > 1080.
    status = _solve_with_setup(target_minutes=960, actual_minutes=0, assigned_shift_count=3)
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_feasible_within_lower_tolerance() -> None:
    """Proves feasibility when the assigned sum sits strictly inside the lower tolerance bound."""
    # Target: 1000, Actual: 0. Range: [880, 1120].
    # 2 shifts = 960m. 880 <= 960 <= 1120.
    status = _solve_with_setup(target_minutes=1000, actual_minutes=0, assigned_shift_count=2)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_feasible_with_preexisting_actual_minutes() -> None:
    """Proves the algebraic delta calculation (target - actual) functions correctly."""
    # Target: 1440, Actual: 480 -> Net Target: 960. Range: [840, 1080].
    # 2 assigned shifts = 960m.
    status = _solve_with_setup(target_minutes=1440, actual_minutes=480, assigned_shift_count=2)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
