from employee import Employee
from day import Day
from shift import Shift
from variables.variable import Variable
from constraints.constraint import Constraint
from ortools.sat.python import cp_model


class SolutionHandler(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        pass

    def on_solution_callback(self):
        pass


class Model:
    def __init__(self):
        self.model = cp_model.Model

    def add_constraints(self, constraints: list[Constraint]):
        for constraint in constraints:
            constraint.add_to_model(self.model)

    def add_at_most_one(self, variables: list[Variable]):
        self.model.add_at_most_one(variables)

    def get_variable(
        self, employee: Employee, day: Day | None, shift: Shift | None
    ) -> str:
        return ""

    def solve(self):
        solver = cp_model.CpSolver()
        handler = SolutionHandler()
        solver.SolveWithSolutionCallback(self.model, handler)
