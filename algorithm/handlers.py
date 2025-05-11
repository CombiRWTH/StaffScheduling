import json
import os
import StateManager
from datetime import datetime
from ortools.sat.python import cp_model


class UnifiedSolutionHandler(cp_model.CpSolverSolutionCallback):
    """Unified handler for solutions (save, print, plot, etc.)."""

    def __init__(
        self, shifts, employees, num_days, num_shifts, limit, case_id, solution_dir
    ):
        super().__init__()
        self._shifts = shifts
        self._employees = employees
        self._num_days = num_days
        self._num_shifts = num_shifts
        self._solution_count = 0
        self._solution_limit = limit
        self._case_id = case_id
        self._solution_dir = solution_dir
        self._constraints = StateManager.state.constraints
        self._solutions = []
        self._employee_name_to_index = {
            employee["name"]: idx for idx, employee in enumerate(employees)
        }

        # Ensure the output directory exists
        os.makedirs(solution_dir, exist_ok=True)

    def on_solution_callback(self):
        self._solution_count += 1
        self.handle_solution()

        if self._solution_limit and self._solution_count >= self._solution_limit:
            self.stop_search()

    def handle_solution(self):
        """Collects the solution triples (n, d, s) for each solution."""
        solution = {}
        for n_idx in range(len(self._employees)):
            for d in range(self._num_days):
                for s in range(self._num_shifts):
                    value = self.Value(self._shifts[(n_idx, d + 1, s)])
                    solution[(n_idx, d + 1, s)] = int(value)
        self._solutions.append(solution)

    def solution_count(self):
        return self._solution_count

    def json(self):
        """Save all collected solutions to a JSON file."""
        output = {
            "caseID": self._case_id,
            "employees": {"name_to_index": self._employee_name_to_index},
            "constraints": self._constraints,
            "numOfSolutions": len(self._solutions),
            "givenSolutionLimit": self._solution_limit,
            "solutions": [
                {str(key): value for key, value in solution.items()}
                for solution in self._solutions
            ],
        }

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(self._solution_dir, f"solutions_{timestamp}.json")

        with open(filename, "w") as f:
            json.dump(output, f, indent=4)

        print(f"Solutions saved to {filename}")

    def print(self):
        """Print collected solutions (not implemented yet)."""
        raise NotImplementedError("Printing solutions is not implemented yet.")

    def plot(self):
        """Plot collected solutions (not implemented yet)."""
        raise NotImplementedError("Plotting solutions is not implemented yet.")
