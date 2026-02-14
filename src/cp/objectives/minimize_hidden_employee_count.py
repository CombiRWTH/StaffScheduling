from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class MinimizeHiddenEmployeeCountObjective(Objective):
    @property
    def KEY(self) -> str:
        return "minimize-hidden-employees"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the objective to minimize overtime for employees.
        Overtime is calculated as the difference between the total working time and the target working time.
        """
        super().__init__(weight, employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        hidden_employee_work_vars: list[IntVar] = []

        for employee in self._employees:
            if not employee.hidden:
                continue

            hidden_employee_is_used = model.new_bool_var(f"hidden_employee_is_used_{employee.get_key()}")
            for day in self._days:
                model.Add(employee_works_on_day_variables[employee][day] <= hidden_employee_is_used)

            hidden_employee_work_vars.append(hidden_employee_is_used)

        return cast(LinearExpr, sum(hidden_employee_work_vars)) * self._weight
