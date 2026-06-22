from collections import defaultdict

from ortools.sat.python import cp_model

from scheduling.solver.cp_sat.context import ObjectiveTerm, SolverContext


def add_balance_generated_assignments_objective(ctx: SolverContext) -> None:
    """Prefer distributing generated assignments across employees."""
    if not ctx.assignment_variables:
        return

    variables_by_employee: defaultdict[int, list[cp_model.IntVar]] = defaultdict(list)

    for key, variable in ctx.assignment_variables.items():
        employee_id, _, _, _, _ = key
        variables_by_employee[employee_id].append(variable)

    generated_counts = [sum(variables) for variables in variables_by_employee.values()]

    max_generated_assignments = ctx.model.new_int_var(
        0,
        len(ctx.assignment_variables),
        "max_generated_assignments_per_employee",
    )

    ctx.model.add_max_equality(max_generated_assignments, generated_counts)

    ctx.objective_terms.append(
        ObjectiveTerm(
            name="balance_generated_assignments",
            expression=max_generated_assignments,
            weight=1,
        )
    )
