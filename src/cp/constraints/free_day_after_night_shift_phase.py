from datetime import timedelta

from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift
from src.station import Station

from ..constants import SPECIAL_NIGHT_SHIFT_INDEX
from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .constraint import Constraint


class FreeDayAfterNightShiftPhaseConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "free-day-after-night-shift-phase"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift], stations: list[Station]):
        """
        Initializes the constraint that ensures an employee has a free day after a night shift phase.
        """
        super().__init__(employees, days, shifts, stations)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> None:
        for employee in self._employees:
            # Iteration bis zum vorletzten Tag, um Index-Out-of-Bounds am Folgetag zu vermeiden
            for day in self._days[:-1]:
                night_vars_today = []
                night_vars_tomorrow = []

                # 1. Aggregation: Sammeln aller Nachtschicht-Variablen (regulär + speziell) über ALLE Stationen
                for station in self._stations:
                    # Heute
                    night_vars_today.append(
                        shift_assignment_variables[employee][day][self._shifts[Shift.NIGHT]][station]
                    )
                    night_vars_today.append(
                        shift_assignment_variables[employee][day][self._shifts[SPECIAL_NIGHT_SHIFT_INDEX]][station]
                    )

                    # Morgen
                    night_vars_tomorrow.append(
                        shift_assignment_variables[employee][day + timedelta(1)][self._shifts[Shift.NIGHT]][station]
                    )
                    night_vars_tomorrow.append(
                        shift_assignment_variables[employee][day + timedelta(1)][
                            self._shifts[SPECIAL_NIGHT_SHIFT_INDEX]
                        ][station]
                    )

                # 2. Verdinglichung (Reification): Boolesche Hilfsvariablen für den Tagesstatus
                works_night_today = model.new_bool_var(f"works_any_night_{employee.get_key()}_{day}")
                model.add_max_equality(works_night_today, night_vars_today)

                works_night_tomorrow = model.new_bool_var(f"works_any_night_tom_{employee.get_key()}_{day}")
                model.add_max_equality(works_night_tomorrow, night_vars_tomorrow)

                day_tomorrow_variable = employee_works_on_day_variables[employee][day + timedelta(1)]

                # 3. Logische Implikation:
                # WENN (heute Nachtschicht == 1) UND (morgen Nachtschicht == 0) DANN (arbeite morgen = 0)
                model.add(day_tomorrow_variable == 0).only_enforce_if([works_night_today, works_night_tomorrow.Not()])
