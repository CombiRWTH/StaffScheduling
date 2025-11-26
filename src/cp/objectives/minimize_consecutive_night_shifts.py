from datetime import timedelta
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class MinimizeConsecutiveNightShiftsObjective(Objective):
    @property
    def KEY(self) -> str:
        return "minimize-consecutive-night-shifts"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the objective that minimizes the number of consecutive night shifts.
        """
        super().__init__(weight, employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        penalties: list[LinearExpr] = []
        # why not cover longer nightn shift phases in this for loop?
        for phase_length in range(2, 5):
            possible_night_shift_phase_variables: list[IntVar] = []
            for employee in self._employees:
                if employee.hidden:
                    continue

                for day in self._days[: -(phase_length - 1)]:
                    night_shift_phase_variable = model.NewBoolVar(
                        f"night_shift_phase_e:{employee.get_key()}_d:{day}_l:{phase_length}"
                    )
                    window = [
                        shift_assignment_variables[employee][day + timedelta(i)][self._shifts[Shift.NIGHT]]
                        for i in range(phase_length)
                    ]
                    model.add_bool_and(window).only_enforce_if(night_shift_phase_variable)
                    model.add_bool_or([night.Not() for night in window]).only_enforce_if(
                        night_shift_phase_variable.Not()
                    )

                    possible_night_shift_phase_variables.append(night_shift_phase_variable)

            penalties.append(cast(LinearExpr, sum(possible_night_shift_phase_variables)) * (self._weight**phase_length))

        return cast(LinearExpr, sum(penalties))
