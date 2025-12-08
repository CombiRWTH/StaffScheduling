from ortools.sat.python.cp_model import CpModel, LinearExpr

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
        # Group days by week
        weeks: dict[int, list[Day]] = {}
        for day in self._days:
            week_number = day.isocalendar().week
            if week_number not in weeks:
                weeks[week_number] = []
            weeks[week_number].append(day)

        # Apply constraints week by week
        for week_days in weeks.values():
            # For each day in this week, store the sum of intermediate shift assignments
            day_intermediate_shift_counts: dict[Day, LinearExpr] = {}

            for day in week_days:
                intermediate_shift_variables: list[Variable] = []

                # Only count non-hidden employees
                for employee in self._employees:
                    if not employee.hidden:
                        intermediate_shift_variables.append(
                            shift_assignment_variables[employee][day][self._shifts[Shift.INTERMEDIATE]]
                        )

                day_intermediate_shift_counts[day] = LinearExpr.Sum(intermediate_shift_variables)  # type: ignore

            # Separate days into weekdays and weekends for this week
            weekdays: list[Day] = []
            weekends: list[Day] = []

            for day in week_days:
                if day.isoweekday() in [6, 7]:  # Saturday or Sunday
                    weekends.append(day)
                else:
                    weekdays.append(day)

            if weekdays and weekends:
                # Add variables that represent max(weekdays), min(weekdays), max(weekends)
                max_weekday = model.NewIntVar(0, len(self._employees), f"max_weekday_{week_days[0].isocalendar().week}")
                min_weekday = model.NewIntVar(0, len(self._employees), f"min_weekday_{week_days[0].isocalendar().week}")
                max_weekend = model.NewIntVar(0, len(self._employees), f"max_weekend_{week_days[0].isocalendar().week}")
                min_weekend = model.NewIntVar(0, len(self._employees), f"min_weekend_{week_days[0].isocalendar().week}")

                model.AddMaxEquality(max_weekday, [day_intermediate_shift_counts[day] for day in weekdays])
                model.AddMinEquality(min_weekday, [day_intermediate_shift_counts[day] for day in weekdays])
                model.AddMaxEquality(max_weekend, [day_intermediate_shift_counts[day] for day in weekends])
                model.AddMinEquality(min_weekend, [day_intermediate_shift_counts[day] for day in weekends])

                # Guarantee that shifts on weekdays and weekends are assigned evenly
                model.Add(max_weekday - min_weekday <= 1)
                model.Add(max_weekend - min_weekend <= 1)

                # Enforce the hierarchy: min(weekdays) <= max(weekends) + 1
                model.Add(max_weekday <= min_weekend + 1)
                model.Add(min_weekday >= max_weekend)
