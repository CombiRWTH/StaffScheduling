import json
import os
import StateManager
from datetime import datetime
from ortools.sat.python import cp_model
from plotting import plot_schedule


class UnifiedSolutionHandler(cp_model.CpSolverSolutionCallback):
    """Unified handler for solutions (save, print, plot, etc.)."""

    def __init__(
        self,
        shifts,
        employees,
        num_days,
        num_shifts,
        dates,
        limit,
        case_id,
        solution_dir,
    ):
        super().__init__()
        self._shifts = shifts
        self._employees = employees
        self._num_days = num_days
        self._num_shifts = num_shifts
        self._dates = dates
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
        solution = {}
        for n_idx in range(len(self._employees)):
            for d in range(self._num_days):
                date_str = self._dates[d].isoformat()
                for s in range(self._num_shifts):
                    value = self.Value(self._shifts[(n_idx, d, s)])
                    solution[(n_idx, date_str, s)] = int(value)
        self._solutions.append(solution)

        self._solution_count += 1
        if self._solution_count >= self._solution_limit:
            self.StopSearch()

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

    def plot(self, solution_index: int = 0):
        """Plot one of the collected solutions by index (default: first)."""

        if not self._solutions:
            raise ValueError("No solutions available to plot.")
        if not (0 <= solution_index < len(self._solutions)):
            raise IndexError(
                f"solution_index must be between 0 and {len(self._solutions) - 1}"
            )

        # Select the solution dict for plotting
        solution = self._solutions[solution_index]

        # Delegate to the schedule-plotting utility
        plot_schedule(
            employees=self._employees,
            schedule=solution,
            dates=self._dates,
        )
