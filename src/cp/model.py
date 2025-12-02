from solution import Solution
from .variables import Variable
from .constraints import Constraint
from .objectives import Objective
from cp.distances.hamming import print_hamming_table
from cp.distances.hungarian import print_hungarian_table
from cp.distances.graph_isomorph import print_iso_matrix
from ortools.sat.python.cp_model import (
    CpModel,
    CpSolver,
    IntVar,
)
import logging
import timeit


from ortools.sat.python import cp_model


class MultiSolutionCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, model, max_solutions=1, max_objective=None):
        super().__init__()
        self.model = model
        self.max_solutions = max_solutions
        self.solutions = []
        self.max_objective = max_objective
        self.count = 0

    def on_solution_callback(self):
        obj = self.ObjectiveValue()
        print("Found Solution with obj value " + str(obj))
        if self.max_objective is not None:
            if obj > self.max_objective:
                return  # ignore low-quality solutions

        if self.count >= self.max_solutions:
            self.StopSearch()
            return

        assignment = {
            name: self.Value(var) for name, var in self.model._variables.items()
        }

        self.solutions.append(
            Solution(
                assignment,
                self.ObjectiveValue(),
            )
        )
        self.count += 1


class Model:
    _model: CpModel
    _variables: dict[str, IntVar]
    _objectives: list[Objective]
    _penalties: list
    _constraints: list[Constraint]

    def __init__(self, max_solutions=2, max_objective=None):
        self._model = CpModel()
        self._variables = {}
        self._objectives = []
        self._penalties = []
        self._constraints = []
        self._max_solutions = max_solutions
        self._max_objective = max_objective

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

        # --- New: Multi-solution callback ---
        collector = MultiSolutionCollector(
            self, max_solutions=self._max_solutions, max_objective=self._max_objective
        )

        logging.info("Searching (optimization, with solution callback)…")

        start_time = timeit.default_timer()
        solver.SolveWithSolutionCallback(self._model, collector)
        elapsed_time = timeit.default_timer() - start_time
        logging.info(f"Solving completed in {elapsed_time:.2f} seconds")
        logging.info(f"Solutions found: {collector.count}")

        print("\nStatistics")
        print(f"  - conflicts      : {solver.num_conflicts}")
        print(f"  - branches       : {solver.num_branches}")
        print(f"  - wall time      : {solver.wall_time} s")
        print(f"  - best objective value: {solver.objective_value}")
        print(f"  - status         : {solver.status_name()}")
        print(f"  - info           : {solver.solution_info()}")

        print("Hamming Distance:")
        print_hamming_table(collector.solutions)
        print("Hungarian Distance:")
        print_hungarian_table(collector.solutions)
        print("Isomorph Graph Matrix")
        print_iso_matrix(collector.solutions)

        return collector.solutions
