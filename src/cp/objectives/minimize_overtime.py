from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeDayShiftVariable, Variable
from .objective import Objective


class MinimizeOvertimeObjective(Objective):
    @property
    def KEY(self) -> str:
        return "minimize-overtime"

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

    def create(self, model: CpModel, variables: dict[str, Variable]) -> LinearExpr:
        possible_overtime_absolute_variables: list[IntVar] = []

        max_duration = 31 * 24 * 60

        for employee in self._employees:
            target_working_time = employee.get_available_working_time()
            possible_working_time: list[LinearExpr] = []

            for day in self._days:
                for shift in self._shifts:
                    variable = cast(IntVar, variables[EmployeeDayShiftVariable.get_key(employee, day, shift)])
                    possible_working_time.append(variable * shift.duration)

            possible_overtime_variable = model.new_int_var(
                -max_duration, max_duration, f"overtime_e:{employee.get_key()}"
            )

            possible_overtime_absolute_variable = model.new_int_var(
                0, max_duration, f"overtime_absolute_e:{employee.get_key()}"
            )
            model.add(possible_overtime_variable == sum(possible_working_time) - target_working_time)
            model.add_abs_equality(
                possible_overtime_absolute_variable,
                possible_overtime_variable,
            )

            possible_overtime_absolute_variables.append(possible_overtime_absolute_variable)

        return cast(LinearExpr, sum(possible_overtime_absolute_variables)) * self._weight
