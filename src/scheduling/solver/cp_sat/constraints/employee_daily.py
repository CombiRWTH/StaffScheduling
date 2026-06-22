from collections import defaultdict

from ortools.sat.python import cp_model

from scheduling.solver.cp_sat.context import SolverContext
from scheduling.solver.cp_sat.keys import EmployeeDateKey


def add_one_assignment_per_employee_day_constraints(ctx: SolverContext) -> None:
    """Prevent more than one generated assignment per employee and day."""
    vars_by_employee_date: defaultdict[EmployeeDateKey, list[cp_model.IntVar]] = defaultdict(list)

    for key, variable in ctx.assignment_variables.items():
        employee_id, _, assignment_date, _, _ = key
        vars_by_employee_date[(employee_id, assignment_date)].append(variable)

    for variables in vars_by_employee_date.values():
        ctx.model.add(sum(variables) <= 1)
