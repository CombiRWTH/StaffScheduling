from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar

from day import Day
from employee import Employee
from shift import Shift

from ..variables import EmployeeDayShiftVariable, Variable
from .constraint import Constraint


class HierarchyOfIntermediateShiftsConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "hierarchy-of-intermediate-shifts"

    def __init__(
        self,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the constraint that introduces a hierarchy to the inter
        mediate shifts. First, one intermediate shift per weekday (Mon-Fri)
        should be assigned. Then one intermediate shift on the weekends,
        then a second intermediate shift on the weekdays and then at the weekends.
        """
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for week in range(self._days[0].isocalendar().week, self._days[-1].isocalendar().week + 1):
            possible_weekday_intermediate_shifts: list[IntVar] = []
            possible_weekend_intermediate_shifts: list[IntVar] = []

            for day in self._days:
                if day.isocalendar().week != week:
                    continue

                intermediate_shift_variables: list[IntVar] = []

                for employee in self._employees:
                    intermediate_shift_variables.append(
                        cast(
                            IntVar,
                            variables[
                                EmployeeDayShiftVariable.get_key(employee, day, self._shifts[Shift.INTERMEDIATE])
                            ],
                        )
                    )

                if day.isoweekday() in [6, 7]:
                    possible_weekend_intermediate_shifts.extend(intermediate_shift_variables)
                else:
                    possible_weekday_intermediate_shifts.extend(intermediate_shift_variables)

            num_of_weekday_intermediate_shifts_variable = model.new_int_var(
                0,
                len(self._employees),
                f"num_of_weekday_intermediate_shifts_variable_w:{week}",
            )
            model.add(num_of_weekday_intermediate_shifts_variable == sum(possible_weekday_intermediate_shifts))

            num_of_weekend_intermediate_shifts_variable = model.new_int_var(
                0,
                len(self._employees),
                f"num_of_weekend_intermediate_shifts_variable_w:{week}",
            )
            model.add(num_of_weekend_intermediate_shifts_variable == sum(possible_weekend_intermediate_shifts))

            model.add(num_of_weekday_intermediate_shifts_variable >= num_of_weekend_intermediate_shifts_variable)
            model.add(num_of_weekday_intermediate_shifts_variable - num_of_weekend_intermediate_shifts_variable <= 1)
