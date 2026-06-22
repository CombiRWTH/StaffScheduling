from scheduling.domain.demand import DemandRequirement
from scheduling.solver.cp_sat.context import SolverContext
from scheduling.solver.cp_sat.eligibility import is_employee_eligible_for_demand
from scheduling.solver.cp_sat.keys import AssignmentVariableKey, DemandKey


def create_assignment_variables(ctx: SolverContext) -> None:
    """Create one boolean variable for each valid generated assignment."""
    for demand in ctx.dataset.demand_requirements:
        if _remaining_required(ctx, demand) <= 0:
            continue

        for employee in ctx.dataset.employees:
            if not is_employee_eligible_for_demand(
                employee=employee,
                demand=demand,
                index=ctx.index,
            ):
                continue

            key: AssignmentVariableKey = (
                employee.employee_id,
                demand.planning_unit_id,
                demand.date,
                demand.shift_id,
                demand.staff_level,
            )

            if key in ctx.assignment_variables:
                continue

            ctx.assignment_variables[key] = ctx.model.new_bool_var(_variable_name(key))


def _remaining_required(ctx: SolverContext, demand: DemandRequirement) -> int:
    demand_key: DemandKey = (
        demand.planning_unit_id,
        demand.date,
        demand.shift_id,
        demand.staff_level,
    )

    required_count = ctx.index.required_count_by_demand_key.get(demand_key, 0)
    fixed_count = ctx.index.fixed_planned_count_by_demand_key.get(demand_key, 0)

    return max(required_count - fixed_count, 0)


def _variable_name(key: AssignmentVariableKey) -> str:
    employee_id, planning_unit_id, assignment_date, shift_id, staff_level = key

    return f"assign_e{employee_id}_p{planning_unit_id}_d{assignment_date.isoformat()}_s{shift_id}_l{staff_level.value}"
