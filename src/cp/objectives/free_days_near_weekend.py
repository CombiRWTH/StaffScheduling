from datetime import timedelta
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class FreeDaysNearWeekendObjective(Objective):
    @property
    def KEY(self) -> str:
        return "free-days-near-weekend"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
    ):
        """
        Initializes the objective that maximizes the number of free days near weekends.
        """
        super().__init__(weight, employees, days, [])

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        possible_free_first_day_variable: list[IntVar] = []
        possible_free_second_day_variables: list[IntVar] = []
        possible_free_both_days_variables: list[IntVar] = []

        for employee in self._employees:
            if employee.hidden:
                continue

            # here we do not ensure that we stay within the month, but we do in the
            # "free_day_after_night_shift_phase.py" file
            for day in self._days:
                if day.isoweekday() in [5, 6, 7]:
                    free_day_variable = model.new_bool_var(f"free_first_day_e:{employee.get_key()}_d:{day}")
                    day_today_variable = employee_works_on_day_variables[employee][day]
                    model.add(day_today_variable == 0).only_enforce_if(free_day_variable)
                    model.add(day_today_variable == 1).only_enforce_if(free_day_variable.Not())

                    possible_free_first_day_variable.append(free_day_variable)

                    if day + timedelta(1) in self._days:
                        free_next_day_variable = model.new_bool_var(
                            f"free_second_day_e:{employee.get_key()}_d:{day + timedelta(1)}"
                        )
                        day_tomorrow_variable = employee_works_on_day_variables[employee][day + timedelta(1)]
                        model.add(day_tomorrow_variable == 0).only_enforce_if(free_next_day_variable)
                        # if day_tomorrow_variable isnt a boolean, than this constraint may be ambiguous
                        model.add(day_tomorrow_variable != 0).only_enforce_if(free_next_day_variable.Not())

                        possible_free_second_day_variables.append(free_next_day_variable)

                        free_both_days_variable = model.new_bool_var(f"free_both_days_e:{employee.get_key()}_d:{day}")
                        model.add_bool_and([free_day_variable, free_next_day_variable]).only_enforce_if(
                            free_both_days_variable
                        )
                        model.add_bool_or(
                            [
                                free_day_variable.Not(),
                                free_next_day_variable.Not(),
                            ]
                        ).only_enforce_if(free_both_days_variable.Not())

                        possible_free_both_days_variables.append(free_both_days_variable)

        return cast(
            LinearExpr,
            sum(
                [
                    sum(possible_free_first_day_variable) * -1 * self.weight,
                    sum(possible_free_second_day_variables) * -1 * self.weight,
                    sum(possible_free_both_days_variables) * -4 * self.weight,
                ]
            ),
        )
