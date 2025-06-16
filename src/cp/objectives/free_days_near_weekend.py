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
        possible_free_saturday_variables: list[IntVar] = []
        possible_free_sunday_variables: list[IntVar] = []
        possible_free_weekend_variables: list[IntVar] = []

        for employee in self._employees:
            for day in self._days:
                if day.isoweekday() in [6]:
                    free_saturday_variable = model.new_bool_var(
                        f"free_saturday_e:{employee.get_id()}_d:{day}"
                    )
                    day_today_variable = variables[
                        EmployeeDayVariable.get_key(employee, day)
                    ]
                    model.add(day_today_variable == 0).only_enforce_if(
                        free_saturday_variable
                    )
                    model.add(day_today_variable == 1).only_enforce_if(
                        free_saturday_variable.Not()
                    )

                    possible_free_saturday_variables.append(free_saturday_variable)

                    if day + timedelta(1) in self._days:
                        free_sunday_variable = model.new_bool_var(
                            f"free_sunday_e:{employee.get_id()}_d:{day + timedelta(1)}"
                        )
                        day_tomorrow_variable = variables[
                            EmployeeDayVariable.get_key(employee, day + timedelta(1))
                        ]
                        model.add(day_tomorrow_variable == 0).only_enforce_if(
                            free_sunday_variable
                        )
                        model.add(day_tomorrow_variable != 0).only_enforce_if(
                            free_sunday_variable.Not()
                        )

                        possible_free_sunday_variables.append(free_sunday_variable)

                        free_weekend_variable = model.new_bool_var(
                            f"free_weekend_e:{employee.get_id()}_d:{day}"
                        )
                        model.add_bool_and(
                            [free_saturday_variable, free_sunday_variable]
                        ).only_enforce_if(free_weekend_variable)
                        model.add_bool_or(
                            [
                                free_saturday_variable.Not(),
                                free_sunday_variable.Not(),
                            ]
                        ).only_enforce_if(free_weekend_variable.Not())

                        possible_free_weekend_variables.append(free_weekend_variable)

        return sum(
            [
                sum(possible_free_saturday_variables) * -1 * self.weight,
                sum(possible_free_sunday_variables) * -1 * self.weight,
                sum(possible_free_weekend_variables) * -2 * self.weight,
            ]
        )
