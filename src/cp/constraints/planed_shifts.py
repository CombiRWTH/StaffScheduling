from . import Constraint
from employee import Employee
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel
import logging


class PlannedShiftsConstraint(Constraint):
    KEY = "planned-shifts"

    # Erweiterte Mapping-Tabelle
    SHIFT_MAPPING = {
        # Standard-Schichten
        "F": 0,  # Frühschicht
        "Z": 1,  # Zwischenschicht
        "S": 2,  # Spätschicht
        "N": 3,  # Nachtschicht
        # Spezielle Schichten
        "Z60": 4,  # Leitungsschicht
        # Alternative Schichtcodes (werden auf Standard gemappt)
        "F2_": 0,  # Frühschicht Variante
        "S2_": 2,  # Spätschicht Variante
        "N5": 3,  # Nachtschicht Variante
    }

    # Nur diese Schichten sind exklusiv (nur für explizit geplante Mitarbeiter)
    EXCLUSIVE_SHIFTS = ["Z60"]

    def __init__(self, employees: list[Employee], days: list, shifts: list[Shift]):
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        # Sammle Mitarbeiter mit exklusiven Schichten
        employees_with_exclusive_shifts = {}

        # Verarbeite alle geplanten Schichten
        for employee in self._employees:
            if not hasattr(employee, "_planned_shifts") or not employee._planned_shifts:
                continue

            for day_num, shift_code in employee._planned_shifts:
                # Tracke exklusive Schichten
                if shift_code in self.EXCLUSIVE_SHIFTS:
                    if shift_code not in employees_with_exclusive_shifts:
                        employees_with_exclusive_shifts[shift_code] = set()
                    employees_with_exclusive_shifts[shift_code].add(employee.get_key())

                # Finde den Tag
                day = next((d for d in self._days if d.day == day_num), None)
                if not day:
                    logging.warning(f"Day {day_num} not found for planned shift")
                    continue

                # Mappe Schichtcode zu ID
                shift_id = self.SHIFT_MAPPING.get(shift_code)
                if shift_id is None:
                    logging.warning(
                        f"Unknown shift code: {shift_code} for {employee.name}"
                    )
                    continue

                # Finde die Schicht
                shift = next((s for s in self._shifts if s.get_id() == shift_id), None)
                if not shift:
                    logging.warning(
                        f"Shift with ID {shift_id} (code: {shift_code}) not found"
                    )
                    continue

                # Setze die geplante Schicht
                variable_key = EmployeeDayShiftVariable.get_key(employee, day, shift)
                if variable_key in variables:
                    model.add(variables[variable_key] == 1)
                else:
                    logging.warning(f"Variable not found: {variable_key}")

                # Verbiete andere Schichten an diesem Tag
                for other_shift in self._shifts:
                    if other_shift.get_id() != shift_id:
                        other_key = EmployeeDayShiftVariable.get_key(
                            employee, day, other_shift
                        )
                        if other_key in variables:
                            model.add(variables[other_key] == 0)

        # Verbiete exklusive Schichten für nicht-autorisierte Mitarbeiter
        for exclusive_shift_code in self.EXCLUSIVE_SHIFTS:
            shift_id = self.SHIFT_MAPPING.get(exclusive_shift_code)
            if shift_id is None:
                continue

            exclusive_shift = next(
                (s for s in self._shifts if s.get_id() == shift_id), None
            )
            if not exclusive_shift:
                continue

            authorized_employees = employees_with_exclusive_shifts.get(
                exclusive_shift_code, set()
            )

            # Verbiete diese Schicht für alle anderen
            for employee in self._employees:
                if employee.get_key() not in authorized_employees:
                    for day in self._days:
                        variable_key = EmployeeDayShiftVariable.get_key(
                            employee, day, exclusive_shift
                        )
                        if variable_key in variables:
                            model.add(variables[variable_key] == 0)
