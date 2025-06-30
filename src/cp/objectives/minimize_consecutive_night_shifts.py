from . import Objective
from ..variables import EmployeeDayShiftVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar
# from datetime import timedelta
#
# class MinimizeConsecutiveNightShiftsObjective(Objective):
#     KEY = "minimize-consecutive-night-shifts"
#
#     def __init__(
#         self,
#         weight: float,
#         employees: list[Employee],
#         days: list[Day],
#         shifts: list[Shift],
#     ):
#         """
#         Initializes the objective that minimizes the number of consecutive night shifts.
#         """
#         super().__init__(weight, employees, days, shifts)
#
#     def create(self, model: CpModel, variables: dict[str, IntVar]):
#         penalties = []
#         for phase_length in range(2, 5):
#             possible_night_shift_phase_variables: list[IntVar] = []
#             for employee in self._employees:
#                 if employee.hidden:
#                     continue
#
#                 for day in self._days[: -(phase_length - 1)]:
#                     night_shift_phase_variable = model.NewBoolVar(
#                         f"night_shift_phase_e:{employee.get_key()}_d:{day}_l:{phase_length}"
#                     )
#                     window = [
#                         variables[
#                             EmployeeDayShiftVariable.get_key(
#                                 employee, day + timedelta(i), self._shifts[Shift.NIGHT]
#                             )
#                         ]
#                         for i in range(phase_length)
#                     ]
#                     model.add_bool_and(window).only_enforce_if(
#                         night_shift_phase_variable
#                     )
#                     model.add_bool_or(
#                         [night.Not() for night in window]
#                     ).only_enforce_if(night_shift_phase_variable.Not())
#
#                     possible_night_shift_phase_variables.append(
#                         night_shift_phase_variable
#                     )
#
#             penalties.append(
#                 sum(possible_night_shift_phase_variables) * (self._weight**phase_length)
#             )
#
#         return sum(penalties)


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
        night_shift = self._shifts[Shift.NIGHT]

        for employee in self._employees:
            if employee.hidden:
                continue

            # get the value list of night shifts of that worker
            employee_shift_vars = [
                variables[EmployeeDayShiftVariable.get_key(employee, day, night_shift)]
                for day in self._days
            ]

            current_streak_vars = []

            for i, var in enumerate(employee_shift_vars):
                if var == 1 and i != len(employee_shift_vars) - 1:
                    current_streak_vars.append(var)
                else:
                    if var == 1 and i == len(employee_shift_vars) - 1:
                        current_streak_vars.append(var)
                    if len(current_streak_vars) >= 2:
                        # legal consecutive night shifts
                        start_index = i - len(current_streak_vars)
                        streak_indicator = model.NewBoolVar(
                            f"night_streak_{employee.get_key()}_{start_index}"
                        )

                        # streak_indicator == 1 ⇔ all the days in that list, the worker works on night shift
                        model.add_bool_and(current_streak_vars).OnlyEnforceIf(
                            streak_indicator
                        )
                        model.add_bool_or(
                            [v.Not() for v in current_streak_vars]
                        ).OnlyEnforceIf(streak_indicator.Not())

                        # penalty
                        penalties.append(
                            streak_indicator
                            * (self._weight ** len(current_streak_vars))
                        )

                    current_streak_vars = []

        return sum(penalties)
