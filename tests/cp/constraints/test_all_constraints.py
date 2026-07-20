import datetime
from contextlib import ExitStack
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from ortools.sat.python import cp_model

from scheduling.domain import (
    Availability,
    AvailabilityType,
    Capability,
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
from scheduling.solver.cp_sat.constraints.availabilities_constraint import AvailabilitiesConstraint
from scheduling.solver.cp_sat.constraints.free_day_after_night_shift_phase import FreeDayAfterNightShiftPhase
from scheduling.solver.cp_sat.constraints.hierarchy_of_intermediate_shifts import HierarchyOfIntermediateShifts
from scheduling.solver.cp_sat.constraints.min_rest_time import MinimumRestTime
from scheduling.solver.cp_sat.constraints.minimum_staffing import MinimumStaffing
from scheduling.solver.cp_sat.constraints.one_assignment_per_day import OneAssignmentPerDay
from scheduling.solver.cp_sat.constraints.rounds_in_early_shift import RoundsInEarlyShift
from scheduling.solver.cp_sat.constraints.target_working_time import TargetWorkingTime
from scheduling.solver.cp_sat.context import create_context

# --- Setup: Global Master Scenario Entities ---

PLANNING_UNIT = PlanningUnit(planning_unit_id=1, display_name="Station 1", type=PlanningUnitType.STATION)

S_EARLY = Shift(
    shift_id=1,
    code="F",
    type=ShiftType.EARLY,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=360,
    end_minute=840,
    net_work_minutes=480,
)
S_LATE = Shift(
    shift_id=2,
    code="S",
    type=ShiftType.LATE,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=840,
    end_minute=1320,
    net_work_minutes=480,
)
S_NIGHT = Shift(
    shift_id=3,
    code="N",
    type=ShiftType.NIGHT,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=1320,
    end_minute=360,
    net_work_minutes=480,
)
S_INTER = Shift(
    shift_id=4,
    code="Z",
    type=ShiftType.EARLY,
    staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
    start_minute=540,
    end_minute=1020,
    net_work_minutes=480,
)

SHIFTS = (S_EARLY, S_LATE, S_NIGHT, S_INTER)

EMPLOYEES = (
    Employee(
        employee_id=1, display_name="E1_Rounds", staff_level=StaffLevel.PROFESSIONAL, capabilities=(Capability.ROUNDS,)
    ),
    Employee(employee_id=2, display_name="E2_Late", staff_level=StaffLevel.PROFESSIONAL),
    Employee(employee_id=3, display_name="E3_Night", staff_level=StaffLevel.PROFESSIONAL),
    Employee(employee_id=4, display_name="E4_Weekend", staff_level=StaffLevel.PROFESSIONAL),
    Employee(employee_id=5, display_name="E5_Inter_WD", staff_level=StaffLevel.PROFESSIONAL),
    Employee(employee_id=6, display_name="E6_Inter_WE", staff_level=StaffLevel.PROFESSIONAL),
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

TEST_DATES = [datetime.date(2024, 11, d) for d in range(4, 11)]


def _solve_master_scenario(
    altered_demands: dict[tuple[datetime.date, int], int] | None = None,
    altered_targets: dict[int, int] | None = None,
    forced_assignments: list[tuple[int, datetime.date, int]] | None = None,
) -> cp_model.CpSolverStatus:
    if altered_demands is None:
        altered_demands = {}
    if altered_targets is None:
        altered_targets = {}
    if forced_assignments is None:
        forced_assignments = []

    targets = {1: 2400, 2: 3360, 3: 2880, 4: 1440, 5: 2400, 6: 480}
    targets.update(altered_targets)

    accounts = [
        MonthlyWorkAccount(employee_id=emp_id, target_minutes=mins, actual_minutes=0)
        for emp_id, mins in targets.items()
    ]

    availabilities = [
        Availability(employee_id=4, date=d, availability_type=AvailabilityType.UNAVAILABLE) for d in TEST_DATES[:4]
    ]

    dataset = SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(PLANNING_UNIT,),
        plans=(),
        shifts=SHIFTS,
        employees=EMPLOYEES,
        planning_unit_memberships=MEMBERSHIPS,
        monthly_work_accounts=tuple(accounts),
        availability=tuple(availabilities),
    )

    ctx = create_context(dataset=dataset)

    for emp in EMPLOYEES:
        for d in TEST_DATES:
            for shift in SHIFTS:
                key = (emp.employee_id, PLANNING_UNIT.planning_unit_id, d, shift.shift_id, StaffLevel.PROFESSIONAL)
                ctx.assignment_variables[key] = ctx.model.new_bool_var(
                    f"assign_{emp.employee_id}_{d:%d}_{shift.shift_id}"
                )

    demands = {}
    for d in TEST_DATES:
        for shift in (S_EARLY, S_LATE, S_NIGHT):
            demands[(PLANNING_UNIT.planning_unit_id, d, shift.shift_id, StaffLevel.PROFESSIONAL)] = 1

        if d.isoweekday() <= 6:
            demands[(PLANNING_UNIT.planning_unit_id, d, S_INTER.shift_id, StaffLevel.PROFESSIONAL)] = 1

    for (d, shift_id), req_count in altered_demands.items():
        demands[(PLANNING_UNIT.planning_unit_id, d, shift_id, StaffLevel.PROFESSIONAL)] = req_count

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "scheduling.solver.cp_sat.constraints.availabilities_constraint.is_night_shift",
                side_effect=lambda s: s.shift_id == 3,  # type: ignore
            )
        )
        stack.enter_context(
            patch(
                "scheduling.solver.cp_sat.constraints.free_day_after_night_shift_phase.is_night_shift",
                side_effect=lambda s: s.shift_id == 3,  # type: ignore
            )
        )
        stack.enter_context(
            patch(
                "scheduling.solver.cp_sat.constraints.hierarchy_of_intermediate_shifts.is_intermediate_shift",
                side_effect=lambda s: s.shift_id == 4,  # type: ignore
            )
        )
        stack.enter_context(
            patch(
                "scheduling.solver.cp_sat.constraints.min_rest_time.is_late_shift",
                side_effect=lambda s: s.shift_id == 2,  # type: ignore
            )
        )
        stack.enter_context(
            patch(
                "scheduling.solver.cp_sat.constraints.min_rest_time.is_early_shift",
                side_effect=lambda s: s.shift_id == 1,  # type: ignore
            )
        )
        stack.enter_context(
            patch(
                "scheduling.solver.cp_sat.constraints.rounds_in_early_shift.is_early_shift",
                side_effect=lambda s: s.shift_id == 1,  # type: ignore
            )
        )

        mock_facts = MagicMock()
        mock_facts.target_working_time_tolerance_less = 0
        mock_facts.target_working_time_tolerance_more = 0
        stack.enter_context(
            patch("scheduling.solver.cp_sat.constraints.target_working_time.facts.TIMEOFFICE_FACTS", mock_facts)
        )

        stack.enter_context(
            patch.object(
                type(ctx.index), "required_count_by_demand_key", new_callable=PropertyMock, return_value=demands
            )
        )

        AvailabilitiesConstraint().add_to_model(ctx, params={})
        FreeDayAfterNightShiftPhase().add_to_model(ctx, params={})
        HierarchyOfIntermediateShifts().add_to_model(ctx, params={})
        MinimumRestTime().add_to_model(ctx, params={})
        MinimumStaffing().add_to_model(ctx, params={})
        OneAssignmentPerDay().add_to_model(ctx, params={})
        RoundsInEarlyShift().add_to_model(ctx, params={})
        TargetWorkingTime().add_to_model(ctx, params={})

    for emp_id, date, fixed_shift_id in forced_assignments:
        key = (emp_id, PLANNING_UNIT.planning_unit_id, date, fixed_shift_id, StaffLevel.PROFESSIONAL)
        ctx.model.add(ctx.assignment_variables[key] == 1)

    solver = cp_model.CpSolver()
    return solver.solve(ctx.model)


# --- Test Cases ---


@pytest.mark.integration
def test_master_scenario_is_perfectly_balanced() -> None:
    status = _solve_master_scenario()
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE)


@pytest.mark.integration
def test_violation_availabilities() -> None:
    status = _solve_master_scenario(forced_assignments=[(4, TEST_DATES[0], S_EARLY.shift_id)])
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_violation_free_day_after_night_shift() -> None:
    """Bricht die Erholungsphase: E3 wird gezwungen, direkt
    am Tag nach einer Nachtschicht in die Frühschicht zu wechseln."""
    status = _solve_master_scenario(
        altered_demands={(TEST_DATES[4], S_EARLY.shift_id): 2},  # Fr Frühschicht braucht 2 Leute
        altered_targets={3: 3360},  # E3 bekommt Budget für 7 Schichten
        forced_assignments=[
            (3, TEST_DATES[3], S_NIGHT.shift_id),  # Donnerstag: E3 macht Nacht
            (3, TEST_DATES[4], S_EARLY.shift_id),  # Freitag: E3 macht Früh -> VIOLATION!
        ],
    )
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_violation_hierarchy_of_intermediate_shifts() -> None:
    status = _solve_master_scenario(
        altered_demands={(TEST_DATES[0], S_INTER.shift_id): 0, (TEST_DATES[-1], S_INTER.shift_id): 1},
        altered_targets={5: 1920, 6: 960},
    )
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_violation_minimum_rest_time() -> None:
    status = _solve_master_scenario(forced_assignments=[(2, TEST_DATES[2], S_EARLY.shift_id)])
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_violation_one_assignment_per_day() -> None:
    status = _solve_master_scenario(
        forced_assignments=[(1, TEST_DATES[0], S_EARLY.shift_id), (1, TEST_DATES[0], S_LATE.shift_id)]
    )
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_violation_rounds_in_early_shift() -> None:
    status = _solve_master_scenario(
        forced_assignments=[(2, TEST_DATES[0], S_EARLY.shift_id), (1, TEST_DATES[0], S_LATE.shift_id)]
    )
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_violation_target_working_time() -> None:
    status = _solve_master_scenario(altered_targets={1: 1920})
    assert status == cp_model.INFEASIBLE


@pytest.mark.integration
def test_violation_minimum_staffing() -> None:
    status = _solve_master_scenario(altered_demands={(TEST_DATES[1], S_NIGHT.shift_id): 2})
    assert status == cp_model.INFEASIBLE
