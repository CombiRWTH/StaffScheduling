from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables, Variable
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

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> None:
        for week in range(self._days[0].isocalendar().week, self._days[-1].isocalendar().week + 1):
            possible_weekday_intermediate_shifts: list[Variable] = []
            possible_weekend_intermediate_shifts: list[Variable] = []

            for day in self._days:
                if day.isocalendar().week != week:
                    continue

                intermediate_shift_variables: list[Variable] = []

                for employee in self._employees:
                    intermediate_shift_variables.append(
                        shift_assignment_variables[employee][day][self._shifts[Shift.INTERMEDIATE]]
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
            # We have to check if this variant is truely more efficient than avoiding the extra variable or not
            model.add(num_of_weekend_intermediate_shifts_variable == sum(possible_weekend_intermediate_shifts))

            # For this to properly work it has to be applied to each day and not to each week. The way it is now
            # there could be 5 intermediate shifts on monday, none on tuesday, wendsday, thursday, friday and 4 on
            # saturday...
            model.add(num_of_weekday_intermediate_shifts_variable >= num_of_weekend_intermediate_shifts_variable)
            model.add(num_of_weekday_intermediate_shifts_variable - num_of_weekend_intermediate_shifts_variable <= 1)
