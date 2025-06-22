from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel


class MinStaffingConstraint(Constraint):
    KEY = "min-staffing"

    _min_staffing: dict[str, dict[str, dict[dict[str, int]]]]

    def __init__(
        self,
        min_staffing: dict[str, dict[str, dict[dict[str, int]]]],
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the constraint that ensures minimum staffing levels for each shift on each day.
        """
        super().__init__(employees, days, shifts)
        self._min_staffing = min_staffing

    def create(self, model: CpModel, variables: dict[str, Variable]):
        weekday_abbreviations = {
            1: "Mo",
            2: "Di",
            3: "Mi",
            4: "Do",
            5: "Fr",
            6: "Sa",
            7: "So",
        }
        shift_abbreviations = {0: "F", 1: "S", 2: "N"}

        for day in self._days:
            weekday = weekday_abbreviations[day.isoweekday()]

            for required_level in self._min_staffing.keys():
                eligible_employees = self._get_eligible_employees(required_level)

                for shift in self._shifts:
                    shift_abbreviation = shift_abbreviations[shift.get_id()]
                    min_staffing = self._min_staffing[required_level][weekday][
                        shift_abbreviation
                    ]

                    potential_working_staff = []
                    for eligible_employee in eligible_employees:
                        variable = variables[
                            EmployeeDayShiftVariable.get_key(
                                eligible_employee, day, shift
                            )
                        ]
                        potential_working_staff.append(variable)

                    model.add(sum(potential_working_staff) >= min_staffing)

    def _get_eligible_employees(self, required_level: str) -> list[Employee]:
        return [
            employee for employee in self._employees if employee.level == required_level
        ]
