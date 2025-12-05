import logging
import timeit
from typing import cast

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import (
    CpModel,
    CpSolver,
    IntVar,
    LinearExpr,
)

from src.solution import Solution

from .constraints import Constraint
from .objectives import Objective
from .variables import Variable


class MultiSolutionCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.solutions = []

    def on_solution_callback(self):
        obj = self.ObjectiveValue()
        print("Found solution with objective:", obj)

        assignment = {name: self.Value(var) for name, var in self.model._variables.items()}

        self.solutions.append(
            Solution(
                assignment,
                self.ObjectiveValue(),
            )
        )


class Model:
    _model: CpModel
    _variables: dict[str, Variable]
    _objectives: list[Objective]
    _penalties: list[LinearExpr]
    _constraints: list[Constraint]

    def __init__(self, max_solutions=1):
        self._model = CpModel()
        self._variables = {}
        self._objectives = []
        self._penalties = []
        self._constraints = []
        self._max_solutions = max_solutions

    def add_constraint(self, constraint: Constraint):
        constraint.create(self._model, self._variables)
        self._constraints.append(constraint)

    def add_objective(self, objective: Objective):
        penalty = objective.create(self._model, self._variables)
        if penalty is not None:
            self._penalties.append(penalty)
        self._objectives.append(objective)

    def add_variable(self, variable: Variable):
        vars = variable.create(self._model, cast(dict[str, IntVar], self._variables))
        for var in vars:
            self._variables[var.name] = cast(Variable, var)

    def solve(self, timeout: int | None) -> Solution:
        logging.info("Solving model...")
        logging.info(f"  - number of variables: {len(self._variables)}")
        logging.info(f"  - number of objectives: {len(self._objectives)}")
        logging.info(f"  - number of constraints: {len(self._constraints)}")

        logging.info("Constraints:")
        for constraint in self._constraints:
            logging.info(f"  - {constraint.name}")

        logging.info("Objectives:")
        for objective in self._objectives:
            logging.info(f"  - {objective.name} (weight: {objective.weight})")

        self._model.minimize(sum(self._penalties))

        solver = CpSolver()
        solver.parameters.num_workers = 0
        if timeout is not None:
            logging.info(f"Timeout set to {timeout} seconds")
            solver.parameters.max_time_in_seconds = timeout

        solver.parameters.linearization_level = 0

        collector = MultiSolutionCollector(self)

        logging.info("Searching (optimization, with solution callback)…")

        start_time = timeit.default_timer()
        solver.SolveWithSolutionCallback(self._model, collector)
        elapsed_time = timeit.default_timer() - start_time
        logging.info(f"Solving completed in {elapsed_time:.2f} seconds")

        print("\nStatistics")
        print(f"  - conflicts      : {solver.num_conflicts}")
        print(f"  - branches       : {solver.num_branches}")
        print(f"  - wall time      : {solver.wall_time} s")
        print(f"  - objective value: {solver.objective_value}")
        print(f"  - status         : {solver.status_name()}")
        print(f"  - objective value: {solver.objective_value}")
        print(f"  - info           : {solver.solution_info()}")

        bestn = sorted(
            collector.solutions,
            key=lambda s: s.objective,
            reverse=True,  # or False depending on maximize/minimize
        )[: self._max_solutions]

        return bestn

        # solution = Solution(
        #     {
        #         cast(IntVar, variable).name: solver.value(cast(IntVar, variable))
        #         for variable in self._variables.values()
        #     },
        #     solver.objective_value,
        # )

        # return solution
