from ortools.sat.python.cp_model import CpModel, Domain, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .constraint import Constraint

TOLERANCE_LESS = 460
TOLERANCE_MORE = TOLERANCE_LESS


class TargetWorkingTimeConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "target-working-time"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint that ensures each employee works a target amount of time.
        """
        super().__init__(employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ):
        working_time_domain = self._get_working_time_domain()

        for employee in self._employees:
            possible_working_time: list[LinearExpr] = []
            for day in self._days:
                for shift in self._shifts:
                    # why are mothly shifts not supposed to count towards the monthly hours?
                    if shift.is_exclusive:
                        continue

                    variable = shift_assignment_variables[employee][day][shift]
                    possible_working_time.append(variable * shift.duration)

            working_time_variable = model.new_int_var_from_domain(
                working_time_domain, f"working_time_e:{employee.get_key()}"
            )
            # is this pattern of variable decleration via conditions realy better for the or tool?
            model.add(sum(possible_working_time) == working_time_variable)

            # who is Milburn Loremarie?
            if employee.name == "Milburn Loremarie":
                continue

            if employee.hidden:
                target_working_time = round(40 * 60 * 4.35)
            else:
                unvavailable_days = set(employee.vacation_days) | set(employee._forbidden_days)  # pyright: ignore[reportPrivateUsage]
                factor = 1 - len(unvavailable_days) / len(self._days)

                # maybe it effects the tool that working_time_domain is probably MUCH larger than
                # target_working_time - TOLERANCE_LESS <= working_time_variable <= target_working_time + TOLERANCE_MORE
                target_working_time = round(
                    max(
                        employee.target_working_time * factor - employee.actual_working_time,
                        0,
                    )
                )

            if employee.hidden:
                # Hidden employees only have an upper limit on working time
                model.add(working_time_variable <= target_working_time + TOLERANCE_MORE)
            else:
                # Regular employees have both upper and lower limits
                model.add(working_time_variable <= target_working_time + TOLERANCE_MORE)
                model.add(working_time_variable >= target_working_time - TOLERANCE_LESS)

    def _get_working_time_domain(self):
        def reachable_sums(others: list[int], max_value: int) -> list[int]:
            reachable: set[int] = set()

            def dfs(current_sum: int):
                if current_sum > max_value:
                    return
                if current_sum in reachable:
                    return
                reachable.add(current_sum)
                for o in others:
                    dfs(current_sum + o)

            dfs(0)  # start from zero
            return sorted(reachable)

        shift_durations = [shift.duration for shift in self._shifts]
        max_duration = max(shift_durations) * len(self._days)

        return Domain.FromValues(reachable_sums(shift_durations, max_duration))
