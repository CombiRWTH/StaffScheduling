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

            employee_night_shift_variables = [
                variables[EmployeeDayShiftVariable.get_key(employee, day, night_shift)]
                for day in self._days
            ]

            current_streak_vars = []

            for i, var in enumerate(
                employee_night_shift_variables + [None]
            ):  # add None to stop the last run
                if var is not None:
                    is_night = model.NewBoolVar(f"is_night_{employee.get_key()}_{i}")
                    model.Add(var == 1).OnlyEnforceIf(is_night)
                    model.Add(var != 1).OnlyEnforceIf(is_night.Not())
                    current_streak_vars.append((var, is_night))
                    streak_bools = [is_night for (_, is_night) in current_streak_vars]
                    is_consecutive = model.NewBoolVar(
                        f"is_consecutive_{employee.get_key()}_{i}"
                    )
                    model.AddBoolAnd(streak_bools).OnlyEnforceIf(is_consecutive)
                    model.AddBoolOr([b.Not() for b in streak_bools]).OnlyEnforceIf(
                        is_consecutive.Not()
                    )
                    penalty = is_consecutive * (self.weight ** len(current_streak_vars))
                    if penalty is not None:
                        continue
                    else:
                        if len(current_streak_vars) >= 3:
                            penalties.append(
                                self.weight ** (len(current_streak_vars) - 1)
                            )
                            current_streak_vars = []
                        else:
                            current_streak_vars = []
                if var is None:
                    streak_bools = [is_night for (_, is_night) in current_streak_vars]
                    is_consecutive = model.NewBoolVar(
                        f"is_consecutive_{employee.get_key()}_{i}"
                    )
                    model.AddBoolAnd(streak_bools).OnlyEnforceIf(is_consecutive)
                    model.AddBoolOr([b.Not() for b in streak_bools]).OnlyEnforceIf(
                        is_consecutive.Not()
                    )
                    penalty = is_consecutive * (self.weight ** len(current_streak_vars))
                    if penalty is not None:
                        if len(current_streak_vars) >= 2:
                            penalties.append(
                                self.weight ** (len(current_streak_vars) - 1)
                            )
                    else:
                        if len(current_streak_vars) >= 3:
                            penalties.append(
                                self.weight ** (len(current_streak_vars) - 1)
                            )
                    current_streak_vars = []
        return sum(penalties)
