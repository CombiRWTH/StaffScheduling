from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel, Domain

TOLERANCE_LESS = 460
TOLERANCE_MORE = TOLERANCE_LESS


class TargetWorkingTimeConstraint(Constraint):
    KEY = "target-working-time"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        working_time_domain = self._get_working_time_domain()

        for employee in self._employees:
            target_working_time = employee.get_target_working_time(self._shifts)

            possible_working_time = []
            for day in self._days:
                for shift in self._shifts:
                    variable = variables[
                        EmployeeDayShiftVariable.get_key(employee, day, shift)
                    ]
                    possible_working_time.append(variable * shift.duration)

            working_time_variable = model.new_int_var_from_domain(
                working_time_domain, f"working_time_e:{employee.get_id()}"
            )

            model.add(sum(possible_working_time) == working_time_variable)
            model.add(working_time_variable <= target_working_time + TOLERANCE_MORE)
            model.add(working_time_variable >= target_working_time - TOLERANCE_LESS)

    def _get_working_time_domain(self):
        def reachable_sums(others, max_value):
            reachable = set()

            def dfs(current_sum):
                if current_sum > max_value:
                    return
                if current_sum in reachable:
                    return
                reachable.add(current_sum)
                for o in others:
                    dfs(current_sum + o)

            dfs(0)  # start from zero
            return sorted(reachable)

        shift_durations = list(map(lambda shift: shift.duration, self._shifts))
        max_duration = max(shift_durations) * len(self._days)

        return Domain.FromValues(reachable_sums(shift_durations, max_duration))
