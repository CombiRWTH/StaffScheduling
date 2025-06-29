from . import Constraint
from employee import Employee
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel
import logging


class PlannedShiftsConstraint(Constraint):
    KEY = "planned-shifts"

    SHIFT_MAPPING = {
        "F": 0,
        "Z": 1,
        "S": 2,
        "N": 3,
        "Z60": 4,
    }

    EXCLUSIVE_SHIFTS = ["Z60"]  # Shifts that can only be assigned with planned_shifts

    def __init__(self, employees: list[Employee], days: list, shifts: list[Shift]):
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        # Collect all employees who are allowed to have Z60 shifts
        employees_with_z60 = set()

        for employee in self._employees:
            if not hasattr(employee, "_planned_shifts") or not employee._planned_shifts:
                continue

            for day_num, shift_code in employee._planned_shifts:
                if shift_code in self.EXCLUSIVE_SHIFTS:
                    employees_with_z60.add(employee.get_key())

                # Existing code für planned shifts...
                day = next((d for d in self._days if d.day == day_num), None)
                if not day:
                    continue

                shift_id = self.SHIFT_MAPPING.get(shift_code)
                if shift_id is None:
                    logging.warning(f"Unknown shift code: {shift_code}")
                    continue

                shift = next((s for s in self._shifts if s.get_id() == shift_id), None)
                if not shift:
                    logging.warning(f"Shift with ID {shift_id} not found")
                    continue

                variable_key = EmployeeDayShiftVariable.get_key(employee, day, shift)
                if variable_key in variables:
                    model.add(variables[variable_key] == 1)

                for other_shift in self._shifts:
                    if other_shift.get_id() != shift_id:
                        other_key = EmployeeDayShiftVariable.get_key(
                            employee, day, other_shift
                        )
                        if other_key in variables:
                            model.add(variables[other_key] == 0)

        # IMPORTANT: Prohibit Z60 for all other employees
        z60_shift = next((s for s in self._shifts if s.get_id() == 4), None)
        if z60_shift:
            for employee in self._employees:
                if employee.get_key() not in employees_with_z60:
                    # This employee is NOT allowed to have a Z60 shift
                    for day in self._days:
                        variable_key = EmployeeDayShiftVariable.get_key(
                            employee, day, z60_shift
                        )
                        if variable_key in variables:
                            model.add(variables[variable_key] == 0)
