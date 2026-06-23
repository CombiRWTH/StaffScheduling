from collections import defaultdict

from ortools.sat.python import cp_model

from scheduling.solver.cp_sat.context import SolverContext, add_objective_term


def add_balance_assignments_objective(ctx: SolverContext) -> None:
    """Prefer distributing generated assignments across employees.

    Temporary migration objective:
    this is a placeholder while the real wish/fairness model is not migrated to
    SchedulingDataset yet. Remove or replace this before final solver evaluation.
    """
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
        "temporary_balance_generated_assignments__max_per_employee",
    )

    ctx.model.add_max_equality(
        max_generated_assignments,
        generated_counts,
    ).with_name("temporary_balance_generated_assignments__define_max_per_employee")

    add_objective_term(
        ctx,
        name="temporary_balance_generated_assignments",
        expression=max_generated_assignments,
        weight=1,
    )
