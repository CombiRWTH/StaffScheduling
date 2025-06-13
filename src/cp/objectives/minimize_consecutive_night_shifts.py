from . import Objective
from ..variables import EmployeeDayShiftVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar
from datetime import timedelta


class MinimizeConsecutiveNightShiftsObjective(Objective):
    KEY = "minimize-consecutive-night-shifts"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        super().__init__(weight, employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        penalties = []
        for phase_length in range(2, 5):
            possible_night_shift_phase_variables: list[IntVar] = []
            for employee in self._employees:
                for day in self._days[: -(phase_length - 1)]:
                    night_shift_phase_variable = model.NewBoolVar(
                        f"night_shift_phase_e:{employee.get_id()}_d:{day}_l:{phase_length}"
                    )
                    window = [
                        variables[
                            EmployeeDayShiftVariable.get_key(
                                employee, day + timedelta(i), self._shifts[Shift.NIGHT]
                            )
                        ]
                        for i in range(phase_length)
                    ]
                    model.add_bool_and(window).only_enforce_if(
                        night_shift_phase_variable
                    )
                    model.add_bool_or(
                        [night.Not() for night in window]
                    ).only_enforce_if(night_shift_phase_variable.Not())

                    possible_night_shift_phase_variables.append(
                        night_shift_phase_variable
                    )

            penalties.append(
                sum(possible_night_shift_phase_variables) * (self._weight**phase_length)
            )

        return sum(penalties)
