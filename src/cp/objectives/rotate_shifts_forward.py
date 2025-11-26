from datetime import timedelta
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class RotateShiftsForwardObjective(Objective):
    @property
    def KEY(self) -> str:
        return "rotate-shifts-forward"

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

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        possible_rotation_variables: list[IntVar] = []
        for employee in self._employees:
            if employee.hidden:
                continue

            for day in self._days[:-1]:
                for shift in self._shifts:
                    rotation_variable = model.new_bool_var(
                        f"rotation_e:{employee.get_key()}_d:{day}_s:{shift.get_id()}"
                    )
                    current_shift_variable = shift_assignment_variables[employee][day][shift]
                    next_desired_shift_variable = shift_assignment_variables[employee][day + timedelta(days=1)][
                        self._shifts[(shift.get_id() + 1) % len(self._shifts)]
                    ]

                    model.add_bool_and([current_shift_variable, next_desired_shift_variable]).only_enforce_if(
                        rotation_variable
                    )
                    model.add_bool_or(
                        [
                            current_shift_variable.Not(),
                            next_desired_shift_variable.Not(),
                        ]
                    ).only_enforce_if(rotation_variable.Not())

                    possible_rotation_variables.append(rotation_variable)

        return cast(LinearExpr, sum(possible_rotation_variables)) * -1 * self.weight
