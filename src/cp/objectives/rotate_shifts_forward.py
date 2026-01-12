from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class RotateShiftsForwardObjective(Objective):
    @property
    def KEY(self) -> str:
        return "rotate-shifts-forward"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the objective that ensures the forward rotation in shifts.
        Forward rotation means: EARLY -> LATE -> NIGHT (never backwards).
        Only checks rotations within a short timeframe (3 days) to avoid penalizing
        natural weekly resets (NIGHT -> EARLY after a rotation cycle is acceptable).
        """
        super().__init__(weight, employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        # Define rotation patterns with their scoring impact
        # Format: (from_shift_type, to_shift_type, is_backward)
        # is_backward=True means penalize, is_backward=False means reward
        rotation_patterns = [
            # Backward rotations (penalize)
            (Shift.LATE, Shift.EARLY, True),  # LATE -> EARLY is backward
            (Shift.NIGHT, Shift.EARLY, True),  # NIGHT -> EARLY is backward
            (Shift.NIGHT, Shift.LATE, True),  # NIGHT -> LATE is backward
            # Forward rotations (reward)
            (Shift.EARLY, Shift.LATE, False),  # EARLY -> LATE is forward
            (Shift.LATE, Shift.NIGHT, False),  # LATE -> NIGHT is forward
        ]

        # Create shift type lookup
        shift_by_type = {shift.get_id(): shift for shift in self._shifts}

        backward_rotation_violations: list[IntVar] = []
        forward_rotation_rewards: list[IntVar] = []

        # Maximum days apart to check for rotations
        # Only check close day pairs (within 3 days) to avoid penalizing natural
        # weekly resets (NIGHT -> EARLY after a week is fine)
        max_days_between = 3

        # Check all employees and day pairs within the time threshold
        for employee in self._employees:
            for day_idx in range(len(self._days)):
                day1 = self._days[day_idx]

                # Check days within the next max_days_between days
                for offset in range(1, min(max_days_between + 1, len(self._days) - day_idx)):
                    day2 = self._days[day_idx + offset]

                    # Check all rotation patterns
                    for from_shift_type, to_shift_type, is_backward in rotation_patterns:
                        # Get the actual shift objects with these types
                        from_shift = shift_by_type.get(from_shift_type)
                        to_shift = shift_by_type.get(to_shift_type)

                        # Skip if shift types don't exist in this problem
                        if from_shift is None or to_shift is None:
                            continue

                        # Create a variable for this rotation pattern
                        rotation_type = "backward" if is_backward else "forward"
                        rotation_var = model.new_bool_var(
                            f"{rotation_type}_rotation_e:{employee.get_key()}_"
                            f"d1:{day1}_s1:{from_shift_type}_"
                            f"d2:{day2}_s2:{to_shift_type}"
                        )

                        # rotation_var is True when employee works from_shift on day1
                        # AND to_shift on day2
                        from_shift_var = shift_assignment_variables[employee][day1][from_shift]
                        to_shift_var = shift_assignment_variables[employee][day2][to_shift]

                        model.add_bool_and([from_shift_var, to_shift_var]).only_enforce_if(rotation_var)
                        model.add_bool_or([from_shift_var.Not(), to_shift_var.Not()]).only_enforce_if(
                            rotation_var.Not()
                        )

                        # Add to appropriate list based on rotation type
                        if is_backward:
                            backward_rotation_violations.append(rotation_var)
                        else:
                            forward_rotation_rewards.append(rotation_var)

        # In minimization: penalties add to cost (+), rewards subtract from cost (-)
        penalty_term = cast(LinearExpr, sum(backward_rotation_violations)) * self.weight
        reward_term = cast(LinearExpr, sum(forward_rotation_rewards)) * self.weight * -1

        return penalty_term + reward_term
