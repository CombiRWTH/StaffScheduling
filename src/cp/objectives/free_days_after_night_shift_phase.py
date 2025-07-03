from . import Objective
from ..variables import EmployeeDayShiftVariable, EmployeeDayVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar


class FreeDaysAfterNightShiftPhaseObjective(Objective):
    KEY = "free-day-after-night-shift-phase"

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

        for employee in self._employees:
            for i in range(len(self._days) - 2):
                day = self._days[i]
                next_day = self._days[i + 1]
                next_next_day = self._days[i + 2]

                # Get night shift variable on current day
                for shift in self._shifts:
                    if shift.get_id() == 3:  # Assuming 3 is night shift
                        night_key = EmployeeDayShiftVariable.get_key(
                            employee, day, shift
                        )
                        if night_key not in variables:
                            continue

                        # Get EmployeeDayVariables for next two days
                        next_day_key = EmployeeDayVariable.get_key(employee, next_day)
                        next_next_day_key = EmployeeDayVariable.get_key(
                            employee, next_next_day
                        )

                        if (
                            next_day_key not in variables
                            or next_next_day_key not in variables
                        ):
                            continue

                        next_day_var = variables[next_day_key]
                        next_next_day_var = variables[next_next_day_key]

                        # Penalize if employee works the next day or the day after that
                        penalty_next_day = model.new_bool_var(
                            f"penalty_next_day_after_night_{employee.get_id()}_{day}"
                        )
                        penalty_next_next_day = model.new_bool_var(
                            f"penalty_second_day_after_night_{employee.get_id()}_{day}"
                        )

                        model.add(next_day_var == 1).only_enforce_if(penalty_next_day)
                        model.add(next_day_var != 1).only_enforce_if(
                            penalty_next_day.Not()
                        )

                        model.add(next_next_day_var == 1).only_enforce_if(
                            penalty_next_next_day
                        )
                        model.add(next_next_day_var != 1).only_enforce_if(
                            penalty_next_next_day.Not()
                        )

                        penalties.append(penalty_next_day)
                        penalties.append(penalty_next_next_day)

        return sum(penalties) * self.weight
