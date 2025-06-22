from . import Objective
from ..variables import EmployeeDayVariable
from employee import Employee
from day import Day
from ortools.sat.python.cp_model import CpModel, IntVar
from datetime import timedelta


class FreeDaysNearWeekendObjective(Objective):
    KEY = "free-days-near-weekend"

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

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        possible_free_first_day_variable: list[IntVar] = []
        possible_free_second_day_variables: list[IntVar] = []
        possible_free_both_days_variables: list[IntVar] = []

        for employee in self._employees:
            for day in self._days:
                if day.isoweekday() in [5, 6, 7]:
                    free_day_variable = model.new_bool_var(
                        f"free_first_day_e:{employee.get_id()}_d:{day}"
                    )
                    day_today_variable = variables[
                        EmployeeDayVariable.get_key(employee, day)
                    ]
                    model.add(day_today_variable == 0).only_enforce_if(
                        free_day_variable
                    )
                    model.add(day_today_variable == 1).only_enforce_if(
                        free_day_variable.Not()
                    )

                    possible_free_first_day_variable.append(free_day_variable)

                    if day + timedelta(1) in self._days:
                        free_next_day_variable = model.new_bool_var(
                            f"free_second_day_e:{employee.get_id()}_d:{day + timedelta(1)}"
                        )
                        day_tomorrow_variable = variables[
                            EmployeeDayVariable.get_key(employee, day + timedelta(1))
                        ]
                        model.add(day_tomorrow_variable == 0).only_enforce_if(
                            free_next_day_variable
                        )
                        model.add(day_tomorrow_variable != 0).only_enforce_if(
                            free_next_day_variable.Not()
                        )

                        possible_free_second_day_variables.append(
                            free_next_day_variable
                        )

                        free_both_days_variable = model.new_bool_var(
                            f"free_both_days_e:{employee.get_id()}_d:{day}"
                        )
                        model.add_bool_and(
                            [free_day_variable, free_next_day_variable]
                        ).only_enforce_if(free_both_days_variable)
                        model.add_bool_or(
                            [
                                free_day_variable.Not(),
                                free_next_day_variable.Not(),
                            ]
                        ).only_enforce_if(free_both_days_variable.Not())

                        possible_free_both_days_variables.append(
                            free_both_days_variable
                        )

        return sum(
            [
                sum(possible_free_first_day_variable) * -1 * self.weight,
                sum(possible_free_second_day_variables) * -1 * self.weight,
                sum(possible_free_both_days_variables) * -4 * self.weight,
            ]
        )
