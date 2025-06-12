from .variables import Variable
from .constraints import Constraint
from .objectives import Objective
from ortools.sat.python.cp_model import (
    CpModel,
    CpSolver,
    CpSolverSolutionCallback,
    IntVar,
)
import logging


class _SolutionHandler(CpSolverSolutionCallback):
    _solutions: int
    _variables: list[IntVar]
    _limit: int

    def __init__(self, variables: list[IntVar], limit: int = 5):
        CpSolverSolutionCallback.__init__(self)
        self._solutions = 0

        self._variables = variables
        self._limit = limit

    def on_solution_callback(self):
        self._solutions += 1
        print(f"Solution {self._solutions}:")

        for variable in self._variables:
            pass
            # print(f"{variable.name}: {self.Value(variable)}")

        if self._solutions >= self._limit:
            self.stop_search()


class Model:
    _model: CpModel
    _variables: dict[str, IntVar]
    _objectives: list[Objective]
    _constraints: list[Constraint]

    def __init__(self):
        self._model = CpModel()
        self._variables = {}
        self._objectives = []
        self._constraints = []

    def add_constraint(self, constraint: Constraint):
        constraint.create(self._model, self._variables)
        self._constraints.append(constraint)

    def add_objective(self, objective: Objective):
        objective.create(self._model, self._variables)
        self._objectives.append(objective)

    def add_variable(self, variable: Variable) -> str:
        vars = variable.create(self._model, self._variables)
        for var in vars:
            self._variables[var.name] = var

    def solve(self, limit: int = 5):
        logging.info("Solving model...")
        logging.info(f"  - number of variables: {len(self._variables)}")
        logging.info(f"  - number of objectives: {len(self._objectives)}")
        logging.info(f"  - number of constraints: {len(self._constraints)}")

        logging.info("Objectives:")
        for objective in self._objectives:
            logging.info(f"  - {objective.name} (weight: {objective.weight})")

        logging.info("Constraints:")
        for constraint in self._constraints:
            logging.info(f"  - {constraint.name}")

        solver = CpSolver()
        solver.parameters.linearization_level = 0
        solver.parameters.enumerate_all_solutions = True
        variables = list(self._variables.values())
        handler = _SolutionHandler(variables, limit)
        solver.SolveWithSolutionCallback(self._model, handler)

        print("\nStatistics")
        print(f"  - conflicts      : {solver.num_conflicts}")
        print(f"  - branches       : {solver.num_branches}")
        print(f"  - wall time      : {solver.wall_time} s")
