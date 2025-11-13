import logging
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar

from day import Day
from employee import Employee
from shift import Shift

from ..variables import EmployeeDayShiftVariable, Variable
from .constraint import Constraint


class PlannedShiftsConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "planned-shifts"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        # Collect employees with exclusive shifts
        employees_with_exclusive_shifts: dict[str, set[int]] = {}
        for employee in self._employees:
            for day_num, shift_code in employee.get_planned_shifts:
                # Track exclusive shifts
                if shift_code in Shift.EXCLUSIVE_SHIFTS:
                    if shift_code not in employees_with_exclusive_shifts:
                        employees_with_exclusive_shifts[shift_code] = set()
                    employees_with_exclusive_shifts[shift_code].add(employee.get_key())

                # Find the day
                day = next((d for d in self._days if d.day == day_num), None)
                if not day:
                    logging.warning(f"Day {day_num} not found for planned shift")
                    continue

                # Map the shift code to ID
                shift_id = Shift.SHIFT_MAPPING.get(shift_code)
                if shift_id is None:
                    logging.warning(f"Unknown shift code: {shift_code} for {employee.name}")
                    continue

                # Find the shift
                shift = self._find_shift_by_id(shift_id)
                if not shift:
                    logging.warning(f"Shift with ID {shift_id} (code: {shift_code}) not found")
                    continue
                # Set the planned shift
                variable_key = EmployeeDayShiftVariable.get_key(employee, day, shift)
                if variable_key in variables:
                    model.add(cast(IntVar, variables[variable_key]) == 1)
                else:
                    raise Exception(f"Variable not found: {variable_key}")

        # Forbidden exclusive shifts for unauthorized employees
        for exclusive_shift_code in Shift.EXCLUSIVE_SHIFTS:
            shift_id = Shift.SHIFT_MAPPING.get(exclusive_shift_code)
            if shift_id is None:
                continue

            exclusive_shift = next((s for s in self._shifts if s.get_id() == shift_id), None)
            if not exclusive_shift:
                continue

            authorized_employees = employees_with_exclusive_shifts.get(exclusive_shift_code, set())

            # Forbidden exclusive shifts for employees not having the shift assigned
            for employee in self._employees:
                if employee.get_key() not in authorized_employees:
                    for day in self._days:
                        variable_key = EmployeeDayShiftVariable.get_key(employee, day, exclusive_shift)
                        if variable_key in variables:
                            model.add(cast(IntVar, variables[variable_key]) == 0)

    def _find_shift_by_id(self, shift_id: int) -> Shift | None:
        for shift in self._shifts:
            if shift.get_id() == shift_id:
                return shift
        return None
