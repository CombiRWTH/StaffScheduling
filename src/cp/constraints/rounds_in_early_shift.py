from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel


class RoundsInEarlyShiftConstraint(Constraint):
    KEY = "rounds-in-early-shift"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        qualified_employees = [
            employee for employee in self._employees if employee.qualified("rounds")
        ]

        for day in self._days:
            if day.isoweekday() in [1, 2, 3, 4, 5]:
                early_shift_variables = [
                    variables[
                        EmployeeDayShiftVariable.get_key(
                            employee, day, self._shifts[Shift.EARLY]
                        )
                    ]
                    for employee in qualified_employees
                ]

                model.add_at_least_one(early_shift_variables)
