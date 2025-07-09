from solution import Solution
from .variables import Variable
from .constraints import Constraint
from .objectives import Objective
from ortools.sat.python.cp_model import (
    CpModel,
    CpSolver,
    IntVar,
)
import logging
import timeit


class Model:
    _model: CpModel
    _variables: dict[str, IntVar]
    _objectives: list[Objective]
    _penalties: list
    _constraints: list[Constraint]

    def __init__(self):
        self._model = CpModel()
        self._variables = {}
        self._objectives = []
        self._penalties = []
        self._constraints = []

    def add_constraint(self, constraint: Constraint):
        constraint.create(self._model, self._variables)
        self._constraints.append(constraint)

    def add_objective(self, objective: Objective):
        penalty = objective.create(self._model, self._variables)
        self._penalties.append(penalty)
        self._objectives.append(objective)

    def add_variable(self, variable: Variable) -> str:
        vars = variable.create(self._model, self._variables)
        for var in vars:
            self._variables[var.name] = var

    def solve(self, timeout: int | None) -> Solution:
        logging.info("Solving model...")
        logging.info(f"  - number of variables: {len(self._variables)}")
        logging.info(f"  - number of objectives: {len(self._objectives)}")
        logging.info(f"  - number of constraints: {len(self._constraints)}")

        logging.info("Objectives:")
        for objective in self._objectives:
            logging.info(f"  - {objective.name} (weight: {objective.weight})")

        self._model.minimize(sum(self._penalties))

        logging.info("Constraints:")
        for constraint in self._constraints:
            logging.info(f"  - {constraint.name}")

        solver = CpSolver()
        solver.parameters.num_workers = 0
        if timeout is not None:
            logging.info(f"Timeout set to {timeout} seconds")
            solver.parameters.max_time_in_seconds = timeout
        solver.parameters.linearization_level = 0

        solver.parameters.stop_after_first_solution = True  # comment out when done
        start_time = timeit.default_timer()

        solver.solve(self._model)
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

        solution = Solution(
            {
                variable.name: solver.value(variable)
                for variable in self._variables.values()
            },
            solver.objective_value,
        )

        return solution
