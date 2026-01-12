import logging
from datetime import timedelta

from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .constraint import Constraint


class EverySecondWeekendFreeConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "every-second-weekend-free"

    def __init__(
        self,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the constraint that enforces alternating free weekends.
        A weekend is defined as Saturday and Sunday, both days must be free.
        """
        super().__init__(employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> None:
        # Collect all complete weekends (Saturday-Sunday pairs) in the planning period
        weekends: list[tuple[Day, Day]] = []

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

            # For each pair of consecutive weekends, enforce alternating pattern
            for i in range(len(weekends) - 1):
                # Get two consecutive weekends
                weekend1_sat, weekend1_sun = weekends[i]
                weekend2_sat, weekend2_sun = weekends[i + 1]

                w1_sat_var = employee_works_on_day_variables[employee][weekend1_sat]
                w1_sun_var = employee_works_on_day_variables[employee][weekend1_sun]
                w2_sat_var = employee_works_on_day_variables[employee][weekend2_sat]
                w2_sun_var = employee_works_on_day_variables[employee][weekend2_sun]

                # Create boolean variables for weekend status
                w1_free = model.new_bool_var(f"w1_free_e:{employee.get_key()}_i:{i}")
                w2_free = model.new_bool_var(f"w2_free_e:{employee.get_key()}_i:{i}")

                # Weekend is free only if both Saturday AND Sunday are free
                model.add(w1_sat_var + w1_sun_var == 0).only_enforce_if(w1_free)
                model.add(w1_sat_var + w1_sun_var >= 1).only_enforce_if(w1_free.Not())

                model.add(w2_sat_var + w2_sun_var == 0).only_enforce_if(w2_free)
                model.add(w2_sat_var + w2_sun_var >= 1).only_enforce_if(w2_free.Not())

                # Hard constraint: two consecutive weekends may not both be worked
                # At least one of the two consecutive weekends must be free
                model.add_bool_or([w1_free, w2_free])
