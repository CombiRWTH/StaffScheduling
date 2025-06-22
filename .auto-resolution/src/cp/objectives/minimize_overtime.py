from . import Objective
from ..variables import EmployeeDayShiftVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar


class MinimizeOvertimeObjective(Objective):
    KEY = "minimize-overtime"

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

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        possible_overtime_absolute_variables: list[IntVar] = []

        max_duration = 31 * 24 * 60

        for employee in self._employees:
            if employee.hidden:
                continue

            target_working_time = employee.get_target_working_time(self._shifts)
            possible_working_time = []

            for day in self._days:
                for shift in self._shifts:
                    variable = variables[
                        EmployeeDayShiftVariable.get_key(employee, day, shift)
                    ]
                    possible_working_time.append(variable * shift.duration)

            possible_overtime_variable = model.new_int_var(
                -max_duration, max_duration, f"overtime_e:{employee.get_id()}"
            )

            possible_overtime_absolute_variable = model.new_int_var(
                0, max_duration, f"overtime_absolute_e:{employee.get_id()}"
            )
            model.add(
                possible_overtime_variable
                == sum(possible_working_time) - target_working_time
            )
            model.add_abs_equality(
                possible_overtime_absolute_variable,
                possible_overtime_variable,
            )

            possible_overtime_absolute_variables.append(
                possible_overtime_absolute_variable
            )

        return sum(possible_overtime_absolute_variables) * self._weight
