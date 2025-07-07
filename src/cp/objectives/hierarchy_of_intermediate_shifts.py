from . import Objective
from ..variables import EmployeeDayShiftVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar


class HierarchyOfIntermediateShifts(Objective):
    KEY = "hierarchy-of-intermediate-shifts"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the objective that introduces a hierarchy to the inter
        mediate shifts. First, one intermediate shift per weekday (Mon-Fri)
        should be assigned. Then one intermediate shift on the weekends,
        then a second intermediate shift on the weekdays and then at the weekends.
        """
        super().__init__(weight, employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        possible_1st_z_shift_on_weekend: list[IntVar] = []
        possible_2nd_z_shift_on_weekend: list[IntVar] = []
        possible_2nd_shift_on_weekday: list[IntVar] = []

        # hidden employees should not have any z shifts
        for employee in self._employees:
            if employee.hidden:
                continue

            for day in self._days:
                # collect all z shifts for the day
                z_today = []
                for employee in self._employees:
                    z_today.append(
                        variables[
                            EmployeeDayShiftVariable.get_key(
                                employee, day, self._shifts[Shift.INTERMEDIATE]
                            )  # intermediate shifts
                        ]
                    )

                is_weekend = day.isoweekday() in [6, 7]  # Saturday or Sunday

                if len(z_today) > 0:
                    # number of z shifts per day
                    total_z_variable = model.NewIntVar(
                        0, len(self._employees), f"total_z_variable_d:{day}"
                    )

                    model.Add(total_z_variable == sum(z_today))

                    # helper variables for single and double z shifts per day
                    is_second_z = model.NewBoolVar(f"is_2nd_z_d:{day}")
                    model.Add(total_z_variable >= 2).OnlyEnforceIf(is_second_z)
                    model.Add(total_z_variable < 2).OnlyEnforceIf(is_second_z.Not())

                    is_any_z = model.NewBoolVar(f"is_any_z_d:{day}")
                    model.Add(total_z_variable >= 1).OnlyEnforceIf(is_any_z)
                    model.Add(total_z_variable < 1).OnlyEnforceIf(is_any_z.Not())

                    if is_weekend:
                        # 1st Z on weekend
                        # 2nd Z on weekend
                        possible_1st_z_shift_on_weekend.append(is_any_z)
                        possible_2nd_z_shift_on_weekend.append(is_second_z)
                    else:
                        # 2nd Z on weekday
                        possible_2nd_shift_on_weekday.append(is_second_z)

        # 1st Z on weekend = +1
        # 2nd Z on weekend = +10 (cumulative, so +9)
        # 2nd Z on weekday = +2
        return sum(
            [
                sum(possible_1st_z_shift_on_weekend) * 1 * self.weight,
                sum(possible_2nd_z_shift_on_weekend) * 9 * self.weight,
                sum(possible_2nd_shift_on_weekday) * 2 * self.weight,
            ]
        )
