from collections import defaultdict
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.domain.shift import ShiftId, ShiftType
from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class RotateShiftsForward:
    """
    Reward forward shift rotations and penalize backward rotations.

    Only assignments on consecutive calendar days are compared.

    Forward:
    - early -> late
    - late -> night

    Backward:
    - late -> early
    - night -> late
    """

    FORWARD_ROTATIONS: ClassVar[tuple[tuple[ShiftType, ShiftType], ...]] = (
        (ShiftType.EARLY, ShiftType.LATE),
        (ShiftType.LATE, ShiftType.NIGHT),
    )

    BACKWARD_ROTATIONS: ClassVar[tuple[tuple[ShiftType, ShiftType], ...]] = (
        (ShiftType.LATE, ShiftType.EARLY),
        (ShiftType.NIGHT, ShiftType.LATE),
    )

    id: ClassVar[str] = "rotate_shifts_forward"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        shift_type_by_shift_id: dict[ShiftId, ShiftType] = {shift.shift_id: shift.type for shift in ctx.dataset.shifts}

        assignment_variables_by_employee_date_and_type: defaultdict[
            tuple[int, date, ShiftType],
            list[cp_model.IntVar],
        ] = defaultdict(list)

        for (
            employee_id,
            _planning_unit_id,
            assignment_date,
            shift_id,
            _qualification_level,
        ), variable in ctx.assignment_variables.items():
            shift_type = shift_type_by_shift_id.get(shift_id)

            if shift_type is None:
                continue

            assignment_variables_by_employee_date_and_type[(employee_id, assignment_date, shift_type)].append(variable)

        employee_ids = sorted(
            {employee_id for employee_id, _planning_unit_id, _date, _shift_id, _level in ctx.assignment_variables}
        )

        shift_worked_variables: dict[
            tuple[int, date, ShiftType],
            cp_model.IntVar,
        ] = {}

        relevant_shift_types = {
            shift_type for rotation in self.FORWARD_ROTATIONS + self.BACKWARD_ROTATIONS for shift_type in rotation
        }

        planning_dates = self._planning_dates(ctx)

        for employee_id in employee_ids:
            for planning_date in planning_dates:
                for shift_type in relevant_shift_types:
                    assignment_variables = assignment_variables_by_employee_date_and_type[
                        (employee_id, planning_date, shift_type)
                    ]

                    worked = ctx.model.new_bool_var(f"rsf_worked_e{employee_id}_d{planning_date}_t{shift_type}")

                    if assignment_variables:
                        ctx.model.add_max_equality(
                            worked,
                            assignment_variables,
                        )
                    else:
                        ctx.model.add(worked == 0)

                    shift_worked_variables[(employee_id, planning_date, shift_type)] = worked

        forward_rotation_variables: list[cp_model.IntVar] = []
        backward_rotation_variables: list[cp_model.IntVar] = []

        for employee_id in employee_ids:
            for current_date in planning_dates:
                next_date = current_date + timedelta(days=1)

                if next_date > ctx.dataset.planning_month.end:
                    continue

                for before_type, after_type in self.FORWARD_ROTATIONS:
                    transition = self._add_transition_variable(
                        ctx=ctx,
                        employee_id=employee_id,
                        current_date=current_date,
                        next_date=next_date,
                        before_type=before_type,
                        after_type=after_type,
                        shift_worked_variables=shift_worked_variables,
                        direction="forward",
                    )
                    forward_rotation_variables.append(transition)

                for before_type, after_type in self.BACKWARD_ROTATIONS:
                    transition = self._add_transition_variable(
                        ctx=ctx,
                        employee_id=employee_id,
                        current_date=current_date,
                        next_date=next_date,
                        before_type=before_type,
                        after_type=after_type,
                        shift_worked_variables=shift_worked_variables,
                        direction="backward",
                    )
                    backward_rotation_variables.append(transition)

        if not forward_rotation_variables and not backward_rotation_variables:
            return ()

        lower_bound = -len(forward_rotation_variables)
        upper_bound = len(backward_rotation_variables)

        rotations = ctx.model.new_int_var(
            lower_bound,
            upper_bound,
            "rsf_rotations",
        )

        ctx.model.add(rotations == sum(backward_rotation_variables) - sum(forward_rotation_variables)).with_name(
            "rotate_shifts_forward__rotations"
        )

        return (
            Penalty(
                objective_id=self.id,
                name="rotations",
                expression=rotations,
            ),
        )

    @staticmethod
    def _add_transition_variable(
        *,
        ctx: SolverContext,
        employee_id: int,
        current_date: date,
        next_date: date,
        before_type: ShiftType,
        after_type: ShiftType,
        shift_worked_variables: Mapping[
            tuple[int, date, ShiftType],
            cp_model.IntVar,
        ],
        direction: str,
    ) -> cp_model.IntVar:
        before_worked = shift_worked_variables[(employee_id, current_date, before_type)]
        after_worked = shift_worked_variables[(employee_id, next_date, after_type)]

        transition = ctx.model.new_bool_var(
            f"rsf_transition_{direction}_e{employee_id}_d{current_date}_{before_type}_{after_type}"
        )

        # For Boolean inputs, min(before, after) is their logical AND.
        ctx.model.add_min_equality(
            transition,
            [before_worked, after_worked],
        )

        return transition

    @staticmethod
    def _planning_dates(ctx: SolverContext) -> tuple[date, ...]:
        dates: list[date] = []

        current_date = ctx.dataset.planning_month.start
        end_date = ctx.dataset.planning_month.end

        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)

        return tuple(dates)

    def audit(self, ctx: AuditContext, params: Mapping[str, Any]) -> tuple[AuditFinding, ...]:
        return ()
