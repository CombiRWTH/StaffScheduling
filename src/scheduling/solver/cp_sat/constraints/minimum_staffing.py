from collections import defaultdict

from ortools.sat.python import cp_model

from scheduling.solver.cp_sat.context import SolverContext
from scheduling.solver.cp_sat.keys import AssignmentVariableKey, DemandKey


def add_minimum_staffing_constraints(ctx: SolverContext) -> None:
    """Cover minimum staffing requirements from SchedulingDataset demand.

    This is the primary dataset-driven hard constraint. It should remain part of
    the final solver model.
    """
    vars_by_demand = _group_vars_by_demand(ctx)

    for demand_key, required_count in ctx.index.required_count_by_demand_key.items():
        fixed_count = ctx.index.fixed_planned_count_by_demand_key.get(demand_key, 0)
        remaining_required = required_count - fixed_count

        if remaining_required <= 0:
            if fixed_count > required_count:
                ctx.diagnostics.append(
                    _overcovered_message(
                        demand_key=demand_key,
                        required_count=required_count,
                        fixed_count=fixed_count,
                    )
                )
            continue

        variables = vars_by_demand.get(demand_key, [])

        if not variables:
            ctx.diagnostics.append(
                _missing_candidates_message(
                    demand_key=demand_key,
                    remaining_required=remaining_required,
                )
            )

        constraint_name = _minimum_staffing_constraint_name(demand_key)
        ctx.model.add(sum(variables) >= remaining_required).with_name(constraint_name)


def _minimum_staffing_constraint_name(demand_key: DemandKey) -> str:
    planning_unit_id, demand_date, shift_id, staff_level = demand_key

    return (
        "minimum_staffing"
        f"__unit_{planning_unit_id}"
        f"__date_{demand_date:%Y%m%d}"
        f"__shift_{shift_id}"
        f"__level_{staff_level.value}"
    )


def _group_vars_by_demand(
    ctx: SolverContext,
) -> dict[DemandKey, list[cp_model.IntVar]]:
    grouped: defaultdict[DemandKey, list[cp_model.IntVar]] = defaultdict(list)

    for key, variable in ctx.assignment_variables.items():
        grouped[_demand_key_from_assignment_key(key)].append(variable)

    return dict(grouped)


def _demand_key_from_assignment_key(key: AssignmentVariableKey) -> DemandKey:
    _, planning_unit_id, assignment_date, shift_id, staff_level = key

    return (
        planning_unit_id,
        assignment_date,
        shift_id,
        staff_level,
    )


def _missing_candidates_message(
    *,
    demand_key: DemandKey,
    remaining_required: int,
) -> str:
    planning_unit_id, demand_date, shift_id, staff_level = demand_key

    return (
        "No eligible candidates for demand "
        f"planning_unit_id={planning_unit_id} "
        f"date={demand_date.isoformat()} "
        f"shift_id={shift_id} "
        f"staff_level={staff_level.value} "
        f"remaining_required={remaining_required}."
    )


def _overcovered_message(
    *,
    demand_key: DemandKey,
    required_count: int,
    fixed_count: int,
) -> str:
    planning_unit_id, demand_date, shift_id, staff_level = demand_key

    return (
        "Existing planned assignments exceed demand "
        f"planning_unit_id={planning_unit_id} "
        f"date={demand_date.isoformat()} "
        f"shift_id={shift_id} "
        f"staff_level={staff_level.value} "
        f"required_count={required_count} "
        f"fixed_count={fixed_count}."
    )
