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
        self._solution_limit = limit
        self._case_id = case_id
        self._solution_dir = solution_dir
        self._constraints = StateManager.state.constraints
        self._solutions = []

        # Ensure the output directory exists
        os.makedirs(solution_dir, exist_ok=True)

    def on_solution_callback(self):
        self.handle_solution()

        if self._solution_limit and len(self._solutions) >= self._solution_limit:
            self.stop_search()

    def handle_solution(self):
        """Collects the solution triples (employee_idx, day_idx, shift_idx) for each solution."""
        solution = {}
        for employee_idx in range(len(self._employees)):
            for day_idx in range(self._num_days):
                for shift_idx in range(self._num_shifts):
                    value = self.Value(self._shifts[(employee_idx, day_idx, shift_idx)])
                    solution[(employee_idx, day_idx, shift_idx)] = int(value)
        self._solutions.append(solution)

    def solution_count(self):
        return len(self._solutions)

    def json(self):
        """Save all collected solutions to a JSON file."""
        output = {
            "caseID": self._case_id,
            "employees": {
                idx: (employee["name"], employee["type"])
                for idx, employee in enumerate(self._employees)
            },
            "constraints": self._constraints,
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
