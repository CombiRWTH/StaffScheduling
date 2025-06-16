from . import Objective
from ..variables import EmployeeDayShiftVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar
from datetime import timedelta


class RotateShiftsForwardObjective(Objective):
    KEY = "rotate-shifts-forward"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the objective that ensures the forward rotation in shifts.
        """
        super().__init__(weight, employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        possible_rotation_variables: list[IntVar] = []
        for employee in self._employees:
            for day in self._days[:-1]:
                for shift in self._shifts:
                    rotation_variable = model.new_bool_var(
                        f"rotation_e:{employee.get_id()}_d:{day}_s:{shift.get_id()}"
                    )
                    current_shift_variable = variables[
                        EmployeeDayShiftVariable.get_key(employee, day, shift)
                    ]
                    next_desired_shift_variable = variables[
                        EmployeeDayShiftVariable.get_key(
                            employee,
                            day + timedelta(days=1),
                            self._shifts[(shift.get_id() + 1) % len(self._shifts)],
                        )
                    ]

                    model.add_bool_and(
                        [current_shift_variable, next_desired_shift_variable]
                    ).only_enforce_if(rotation_variable)
                    model.add_bool_or(
                        [
                            current_shift_variable.Not(),
                            next_desired_shift_variable.Not(),
                        ]
                    ).only_enforce_if(rotation_variable.Not())

                    possible_rotation_variables.append(rotation_variable)

        return sum(possible_rotation_variables) * -1 * self.weight
