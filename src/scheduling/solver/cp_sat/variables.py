from datetime import date, timedelta

from scheduling.domain import PlanningUnitType, StaffingDemandRole
from scheduling.solver.cp_sat.context import SolverContext
from scheduling.solver.cp_sat.eligibility import eligible_staff_levels_for_assignment_slot
from scheduling.solver.cp_sat.keys import AssignmentVariableKey


def create_assignment_variables(ctx: SolverContext) -> None:
    """Create one boolean variable for every feasible generated assignment slot.

    Long-term model direction:
    variables describe the possible schedule space. Demand, wishes, fairness,
    and workload rules are separate constraints/objectives over that space.
    """
    for planning_unit_id in _assignable_planning_unit_ids(ctx):
        for assignment_date in _planning_dates(ctx):
            for shift_id in _assignable_shift_ids(ctx):
                for employee in ctx.dataset.employees:
                    staff_levels = eligible_staff_levels_for_assignment_slot(
                        employee=employee,
                        planning_unit_id=planning_unit_id,
                        assignment_date=assignment_date,
                        shift_id=shift_id,
                        index=ctx.index,
                    )

                    for staff_level in staff_levels:
                        key: AssignmentVariableKey = (
                            employee.employee_id,
                            planning_unit_id,
                            assignment_date,
                            shift_id,
                            staff_level,
                        )

                        ctx.assignment_variables[key] = ctx.model.new_bool_var(_assignment_variable_name(key))


def _assignable_planning_unit_ids(ctx: SolverContext) -> tuple[int, ...]:
    return tuple(
        sorted(
            planning_unit.planning_unit_id
            for planning_unit in ctx.dataset.planning_units
            if planning_unit.type == PlanningUnitType.STATION
        )
    )


def _assignable_shift_ids(ctx: SolverContext) -> tuple[int, ...]:
    return tuple(
        sorted(
            shift.shift_id for shift in ctx.dataset.shifts if shift.staffing_role != StaffingDemandRole.NON_MINIMUM_WORK
        )
    )


def _planning_dates(ctx: SolverContext) -> tuple[date, ...]:
    dates: list[date] = []

    current_date = ctx.dataset.planning_month.start
    while current_date <= ctx.dataset.planning_month.end:
        dates.append(current_date)
        current_date += timedelta(days=1)

    return tuple(dates)


def _assignment_variable_name(key: AssignmentVariableKey) -> str:
    employee_id, planning_unit_id, assignment_date, shift_id, staff_level = key

    return (
        "assign"
        f"__employee_{employee_id}"
        f"__unit_{planning_unit_id}"
        f"__date_{assignment_date:%Y%m%d}"
        f"__shift_{shift_id}"
        f"__level_{staff_level.value}"
    )
