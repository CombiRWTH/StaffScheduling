from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayVariable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel
from datetime import timedelta


class VacationDaysAndShiftsConstraint(Constraint):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__("vaction-days-and-shifts", employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            for day in self._days:
                if employee.has_vacation(day.day):
                    day_var = variables[EmployeeDayVariable.get_key(employee, day)]
                    model.add(day_var == 0)

                    if day.day > 1:
                        night_shift_var = variables[
                            EmployeeDayShiftVariable.get_key(
                                employee, day - timedelta(1), self._shifts[Shift.NIGHT]
                            )
                        ]
                        model.add(night_shift_var == 0)

                for shift in self._shifts:
                    if employee.has_vacation(day.day, shift.get_id()):
                        shift_var = variables[
                            EmployeeDayShiftVariable.get_key(employee, day, shift)
                        ]
                        model.add(shift_var == 0)
