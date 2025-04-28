import json
from ortools.sat.python import cp_model
from plotting import plot_schedule
from building_constraints.free_shifts_and_vacation_days import (
    load_free_shifts_and_vacation_days,
    add_free_shifts_and_vacatian_days,
)
from building_constraints.target_working_hours import (
    load_target_working_hours,
    add_target_working_hours,
)


def load_employees(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data["employees"]

def load_general_settings(filename):
    with open(filename, "r") as f:
        config = json.load(f)
    return config

def load_staff_requirements(filename):
    with open(filename, "r") as f:
        return json.load(f)["requirements"]


def create_shift_variables(model, employees, num_days, num_shifts):
    shifts = {}
    for n_idx, employee in enumerate(employees):
        for d in range(num_days):
            for s in range(num_shifts):
                shifts[(n_idx, d, s)] = model.new_bool_var(
                    f"shift_{employee['name']}_d{d}_s{s}"
                )
    return shifts


def add_basic_constraints(
    model, employees, shifts, num_days, num_shifts
):
    num_employees = len(employees)
    all_employees = range(num_employees)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    # one employee per (name, day, shift) tuple
    for d in all_days:
        for s in all_shifts:
            model.add_exactly_one(
                shifts[(n, d, s)] for n in all_employees
            )

    # one shift per employee per day at most
    for n in all_employees:
        for d in all_days:
            model.add_at_most_one(shifts[(n, d, s)] for s in all_shifts)


def add_staff_type_requirements(
    model, employees, shifts, requirements, num_days, num_shifts
):
    employeeidx_by_type = {}
    for idx, employee in enumerate(employees):
        employeeidx_by_type.setdefault(employee["type"], []).append(idx)

    for req in requirements:
        day = req["day"]
        shift = req["shift"]
        for staff_type, required_count in req["required"].items():
            if staff_type not in employeeidx_by_type:
                continue
            relevant_employees = employeeidx_by_type[staff_type]
            work_vars = [
                shifts[(n, day, shift)] for n in relevant_employees
            ]
            model.Add(sum(work_vars) == required_count)


def solve_and_print(
    model, employees, shifts, num_days, num_shifts, solution_limit=10
):
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.linearization_level = 0

    class employeesolutionPrinter(cp_model.CpSolverSolutionCallback):
        def __init__(
            self, shifts, employees, num_days, num_shifts, limit
        ):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self._shifts = shifts
            self._employees = employees
            self._num_days = num_days
            self._num_shifts = num_shifts
            self._solution_count = 0
            self._solution_limit = limit

        def on_solution_callback(self):
            self._solution_count += 1
            print(f"\nSolution {self._solution_count}")
            for d in range(self._num_days):
                print(f" Day {d}:")
                for n_idx, employee in enumerate(self._employees):
                    worked = False
                    for s in range(self._num_shifts):
                        if self.value(self._shifts[(n_idx, d, s)]):
                            worked = True
                            print(
                                f"  {employee['name']} ({employee['type']}) works shift {s}"
                            )
                    if not worked:
                        print(
                            f"  {employee['name']} ({employee['type']}) has the day off."
                        )

            if (
                self._solution_limit
                and self._solution_count >= self._solution_limit
            ):
                self.stop_search()

        def solution_count(self):
            return self._solution_count

    solution_printer = employeesolutionPrinter(
        shifts, employees, num_days, num_shifts, solution_limit
    )
    solver.solve(model, solution_printer)

    print("\nStatistics")
    print(f"  - Conflicts     : {solver.num_conflicts}")
    print(f"  - Branches      : {solver.num_branches}")
    print(f"  - Wall time     : {solver.wall_time:.2f}s")
    print(f"  - Solutions found: {solution_printer.solution_count()}")


def solve_and_plot(
    model, employees, shifts, num_days, num_shifts, solution_limit=10
):
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.linearization_level = 0

    schedule = {}

    class employeesolutionCollector(cp_model.CpSolverSolutionCallback):
        def __init__(
            self, shifts, employees, num_days, num_shifts, limit
        ):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self._shifts = shifts
            self._employees = employees
            self._num_days = num_days
            self._num_shifts = num_shifts
            self._solution_count = 0
            self._solution_limit = limit
            self._schedule = {}

        def on_solution_callback(self):
            if self._solution_count == 0:
                for n_idx in range(len(self._employees)):
                    for d in range(self._num_days):
                        for s in range(self._num_shifts):
                            if self.Value(self._shifts[(n_idx, d, s)]):
                                self._schedule[(n_idx, d, s)] = True
            self._solution_count += 1
            if (
                self._solution_limit
                and self._solution_count >= self._solution_limit
            ):
                self.stop_search()

        def get_schedule(self):
            return self._schedule

    solution_collector = employeesolutionCollector(
        shifts, employees, num_days, num_shifts, solution_limit
    )
    solver.solve(model, solution_collector)

    print("\nStatistics")
    print(f"  - Conflicts     : {solver.num_conflicts}")
    print(f"  - Branches      : {solver.num_branches}")
    print(f"  - Wall time     : {solver.wall_time:.2f}s")
    print(f"  - Solutions found: {solution_collector._solution_count}")

    schedule = solution_collector.get_schedule()
    plot_schedule(employees, schedule, num_days)


def main():
    CASE_ID = 1

    employees = load_employees(f"./cases/{CASE_ID}/employees.json")
    free_shifts_and_vacation_days = load_free_shifts_and_vacation_days(
        f"./cases/{CASE_ID}/free_shifts_and_vacation_days.json"
    )
    target_hours, shift_durations, tolerance_hours = (
        load_target_working_hours(
            f"./cases/{CASE_ID}/target_working_hours.json",
            f"./cases/{CASE_ID}/general_settings.json",
        )
    )
    # staff_requirements = load_staff_requirements(
    #     "staff_requirements.json"
    # )

    num_days = 30
    num_shifts = 3

    model = cp_model.CpModel()

    shifts = create_shift_variables(
        model, employees, num_days, num_shifts
    )
    add_basic_constraints(
        model, employees, shifts, num_days, num_shifts
    )
    add_free_shifts_and_vacatian_days(
        model,
        employees,
        shifts,
        free_shifts_and_vacation_days,
        num_days,
        num_shifts,
    )
    # add_staff_type_requirements(
    #     model, employees, shifts, staff_requirements, num_days, num_shifts
    # )
    add_target_working_hours(
        model,
        employees,
        shifts,
        num_days,
        num_shifts,
        shift_durations,
        target_hours,
        tolerance_hours,
    )

    solve_and_plot(model, employees, shifts, num_days, num_shifts, solution_limit=1)
    #solve_and_print(
    #     model,
    #     employees,
    #     shifts,
    #     num_days,
    #     num_shifts,
    #     solution_limit=10,
    # )


if __name__ == "__main__":
    main()
