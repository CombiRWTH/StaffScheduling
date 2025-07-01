from . import Objective
from ..variables import EmployeeDayShiftVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar


class MinimizeConsecutiveNightShiftsObjective(Objective):
    KEY = "minimize-consecutive-night-shifts"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the objective that minimizes the number of consecutive night shifts.
        """
        super().__init__(weight, employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        penalties = []

        night_shift = self._shifts[Shift.NIGHT]

        for employee in self._employees:
            if employee.hidden:
                continue

            # get the variable list, which represent if that worker work on night shift on each days
            employee_shift_vars = [
                variables[EmployeeDayShiftVariable.get_key(employee, day, night_shift)]
                for day in self._days
            ]

            current_streak_vars = []

            for i, var in enumerate(
                employee_shift_vars + [None]
            ):  # add None to stop the last run
                if var is not None:
                    is_night = model.NewBoolVar(f"is_night_{employee.get_key()}_{i}")
                    model.Add(var == 1).OnlyEnforceIf(is_night)
                    model.Add(var != 1).OnlyEnforceIf(is_night.Not())

                    current_streak_vars.append((var, is_night))
                if var is None or (
                    i > 0
                    and current_streak_vars
                    and current_streak_vars[-1][1] is not None
                ):
                    if len(current_streak_vars) >= 2:
                        # legal consecutive night shifts
                        start_index = i - len(current_streak_vars)
                        streak_indicator = model.NewBoolVar(
                            f"night_streak_{employee.get_key()}_{start_index}"
                        )
                        streak_bools = [
                            is_night for (_, is_night) in current_streak_vars
                        ]

                        # streak_indicator == 1 ⇔ all days are night shift
                        model.AddBoolAnd(streak_bools).OnlyEnforceIf(streak_indicator)
                        model.AddBoolOr([b.Not() for b in streak_bools]).OnlyEnforceIf(
                            streak_indicator.Not()
                        )

                        # Index penalties
                        penalties.append(
                            streak_indicator * (self.weight ** len(streak_bools))
                        )
                    current_streak_vars = []

        return sum(penalties)
