from collections import defaultdict
from collections.abc import Mapping
from datetime import date as Date
from typing import Any, ClassVar

from scheduling.domain.shift import ShiftId, ShiftType
from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class RotateShiftsForward:
    """
    Adds a reward for each time an employee works forward rotating shifts and a
    penalty for backwards rotating shifts
    """

    FORWARD_ROTATIONS = ((ShiftType("early"), ShiftType("late")), (ShiftType("late"), ShiftType("night")))
    BACKWARD_ROTATIONS = (
        (ShiftType("late"), ShiftType("early")),
        (ShiftType("night"), ShiftType("late")),
        # In the legacy version, they also penalize going from night -> early, which makes no sense in my eyes
        # Also, they only consider a timeframe of 3 days per shift, I do not understand why
    )

    id: ClassVar[str] = "rotate_shifts_forward"

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        # First check which shifts every employee is assigned to
        days_by_employee: dict[int, list[tuple[Date, ShiftId]]] = defaultdict[int, list[tuple[Date, ShiftId]]](list)
        for key, _variable in ctx.assignment_variables.items():
            employee_id, _, date, shift_id, _ = key
            days_by_employee[employee_id].append((date, shift_id))

        # Find out how the shifts rotate for each employee
        num_forward_rotations: int = 0
        num_backward_rotations: int = 0
        for employee_id in days_by_employee.keys():
            # Again make sure that the shifts are properly sorted
            days_by_employee[employee_id] = sorted(days_by_employee[employee_id])

            for i in range(len(days_by_employee[employee_id]) - 1):
                for shift in ctx.dataset.shifts:
                    if shift.shift_id == days_by_employee[employee_id][i][1]:
                        shift_type_before = shift.type
                    if shift.shift_id == days_by_employee[employee_id][i + 1][1]:
                        shift_type_after = shift.type
                if (shift_type_before, shift_type_after) in self.FORWARD_ROTATIONS:
                    num_forward_rotations += 1
                elif (shift_type_before, shift_type_after) in self.BACKWARD_ROTATIONS:
                    num_backward_rotations += 1

        rotations = ctx.model.new_int_var(-1000000, 1000000, "rotations")

        ctx.model.add(rotations == num_backward_rotations - num_forward_rotations).with_name(
            "rotate_shifts_forward__rotations"
        )

        return (
            Penalty(
                objective_id=self.id,
                name="rotations",
                expression=rotations,
            ),
        )

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        return ()
