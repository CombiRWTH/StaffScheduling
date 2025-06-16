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
        possible_overtime_variables: list[IntVar] = []

        shift_durations = list(map(lambda shift: shift.duration, self._shifts))
        max_duration = max(shift_durations) * len(self._days)

        for employee in self._employees:
            target_working_time = employee.get_target_working_time(self._shifts)
            possible_working_time = []

            for day in self._days:
                for shift in self._shifts:
                    variable = variables[
                        EmployeeDayShiftVariable.get_key(employee, day, shift)
                    ]
                    possible_working_time.append(variable * shift.duration)

            possible_overtime_variable = model.new_int_var(
                0, max_duration, f"overtime_e:{employee.get_id()}"
            )

            model.add_abs_equality(
                possible_overtime_variable,
                sum(possible_working_time) - target_working_time,
            )
            possible_overtime_variables.append(possible_overtime_variable)

        return sum(possible_overtime_variables) * self._weight
