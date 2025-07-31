from . import Objective
from ..variables import EmployeeDayVariable
from employee import Employee
from day import Day
from ortools.sat.python.cp_model import CpModel, IntVar
from datetime import timedelta
import logging


class EverySecondWeekendFreeObjective(Objective):
    KEY = "every-second-weekend-free"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list = [],
    ):
        """
        Initializes the objective that encourages alternating free weekends.
        A weekend is defined as Saturday and Sunday, both days must be free.
        """
        super().__init__(weight, employees, days, [])

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        penalties: list[IntVar] = []

        # Collect all complete weekends (Saturday-Sunday pairs) in the planning period
        weekends = []

        for day in self._days:
            # Check if this day is a Saturday (isoweekday: Monday=1, ..., Saturday=6, Sunday=7)
            is_saturday = day.isoweekday() == 6

            if is_saturday:
                # Calculate the next day (Sunday)
                next_day = day + timedelta(days=1)

                # Only add this weekend if Sunday is also in our planning period
                sunday_is_in_planning_period = next_day in self._days

                if sunday_is_in_planning_period:
                    saturday = day
                    sunday = next_day
                    weekend_pair = (saturday, sunday)
                    weekends.append(weekend_pair)

        logging.info(f"Found {len(weekends)} complete weekends in the planning period")

        for employee in self._employees:
            if employee.hidden:
                continue

            # For each pair of consecutive weekends, penalize if both are free or both have work
            for i in range(len(weekends) - 1):
                # Get two consecutive weekends
                weekend1_sat, weekend1_sun = weekends[i]
                weekend2_sat, weekend2_sun = weekends[i + 1]
                w1_sat_var = variables[
                    EmployeeDayVariable.get_key(employee, weekend1_sat)
                ]
                w1_sun_var = variables[
                    EmployeeDayVariable.get_key(employee, weekend1_sun)
                ]
                w2_sat_var = variables[
                    EmployeeDayVariable.get_key(employee, weekend2_sat)
                ]
                w2_sun_var = variables[
                    EmployeeDayVariable.get_key(employee, weekend2_sun)
                ]

                # Check if weekends are free (both days must be free)
                w1_free = model.new_bool_var(f"w1_free_e:{employee.get_key()}_i:{i}")
                w2_free = model.new_bool_var(f"w2_free_e:{employee.get_key()}_i:{i}")

                # Weekend is free only if both Saturday AND Sunday are free
                model.add(w1_sat_var + w1_sun_var == 0).only_enforce_if(w1_free)
                model.add(w1_sat_var + w1_sun_var >= 1).only_enforce_if(w1_free.Not())

                model.add(w2_sat_var + w2_sun_var == 0).only_enforce_if(w2_free)
                model.add(w2_sat_var + w2_sun_var >= 1).only_enforce_if(w2_free.Not())
                same_status_penalty = model.new_bool_var(
                    f"same_status_penalty_e:{employee.get_key()}_i:{i}"
                )

                # Penalty = 1 if (w1_free AND w2_free) OR (NOT w1_free AND NOT w2_free)
                model.add(same_status_penalty == 1).only_enforce_if([w1_free, w2_free])
                model.add(same_status_penalty == 1).only_enforce_if(
                    [w1_free.Not(), w2_free.Not()]
                )
                model.add(same_status_penalty == 0).only_enforce_if(
                    [w1_free, w2_free.Not()]
                )
                model.add(same_status_penalty == 0).only_enforce_if(
                    [w1_free.Not(), w2_free]
                )

                penalties.append(same_status_penalty)

        return sum(penalties) * self.weight
