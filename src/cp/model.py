import logging
import timeit
from typing import cast

from ortools.sat.python.cp_model import (
    CpModel,
    CpSolver,
    IntVar,
    LinearExpr,
)

from src.day import Day
from src.employee import Employee
from src.shift import Shift
from src.solution import Solution

from .constraints import Constraint
from .objectives import Objective
from .variables import (
    EmployeeWorksOnDayVariables,
    ShiftAssignmentVariables,
    Variable,
    create_employee_works_on_day_variables,
    create_shift_assignment_variables,
    setup_employee_works_on_day_variables,
)


class Model:
    _model: CpModel
    _shiftAssignmentVariables: ShiftAssignmentVariables
    _employeeWorksOnDayVariables: EmployeeWorksOnDayVariables
    _employees: list[Employee]
    _days: list[Day]
    _shifts: list[Shift]
    _objectives: list[Objective]
    _penalties: list[LinearExpr]
    _constraints: list[Constraint]

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        self._model = CpModel()
        self._employees = employees
        self._days = days
        self._shifts = shifts
        self._objectives = []
        self._penalties = []
        self._constraints = []
        self._shiftAssignmentVariables = create_shift_assignment_variables(
            self._employees,
            self._days,
            self._shifts,
            self._model,
        )
        self._employeeWorksOnDayVariables = create_employee_works_on_day_variables(
            self._employees,
            self._days,
            self._model,
        )
        setup_employee_works_on_day_variables(
            self._shiftAssignmentVariables,
            self._employeeWorksOnDayVariables,
            self._employees,
            self._days,
            self._shifts,
            self._model,
        )

    @property
    def variables(self) -> list[Variable]:
        return self._variables

    @property
    def _variables(self) -> list[Variable]:
        """Creates a dictionary mapping variable names to Variable objects."""
        variables: list[Variable] = []

        # Add shift assignment variables
        for employee in self._employees:
            for day in self._days:
                for shift in self._shifts:
                    var = self._shiftAssignmentVariables[employee][day][shift]
                    variables.append(var)

        # Add employee works on day variables
        for employee in self._employees:
            for day in self._days:
                var = self._employeeWorksOnDayVariables[employee][day]
                variables.append(var)

        return variables

    @property
    def shift_assignment_variables(self) -> ShiftAssignmentVariables:
        return self._shiftAssignmentVariables

    @property
    def employee_works_on_day_variables(self) -> EmployeeWorksOnDayVariables:
        return self._employeeWorksOnDayVariables

    @property
    def cpModel(self) -> CpModel:
        return self._model

    @property
    def employees(self) -> list[Employee]:
        return self._employees

    # Warning: Only use this setter in tests to limit the employees to a subset for violation checks
    @employees.setter
    def employees(self, value: list[Employee]):
        self._employees = value

    @property
    def days(self) -> list[Day]:
        return self._days

    @property
    def shifts(self) -> list[Shift]:
        return self._shifts

    @property
    def penalties(self) -> list[LinearExpr]:
        return self._penalties

    def add_constraint(self, constraint: Constraint):
        constraint.create(self._model, self._shiftAssignmentVariables, self._employeeWorksOnDayVariables)
        self._constraints.append(constraint)

    def add_objective(self, objective: Objective):
        penalty = objective.create(self._model, self._shiftAssignmentVariables, self._employeeWorksOnDayVariables)
        if penalty is not None:
            self._penalties.append(penalty)
        self._objectives.append(objective)

    def solve(self, timeout: int | None) -> Solution:
        logging.info("Solving model...")
        logging.info(
            f"  - number of variables: {len(self._shiftAssignmentVariables) + len(self._employeeWorksOnDayVariables)}"
        )
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
            {cast(IntVar, variable).name: solver.value(variable) for variable in self._variables},
            solver.objective_value,
        )

        return solution
