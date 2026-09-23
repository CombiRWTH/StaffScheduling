from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.domain.shift import ShiftType
from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class MinimizeConsecutiveNightShifts:
    """
    Penalize consecutive night-shift windows of lengths 2, 3, and 4.

    Each phase length produces a separate penalty.
    """

    id: ClassVar[str] = "minimize_consecutive_night_shifts"
    PHASE_LENGTHS: ClassVar[tuple[int, ...]] = (2, 3, 4)

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        night_shift_ids = {shift.shift_id for shift in ctx.dataset.shifts if shift.type == ShiftType.NIGHT}
        if not night_shift_ids:
            return ()

        night_assignment_variables: defaultdict[
            tuple[int, date],
            list[cp_model.IntVar],
        ] = defaultdict(list)

        for (
            employee_id,
            _planning_unit_id,
            assignment_date,
            shift_id,
            _qualification_level,
        ), variable in ctx.assignment_variables.items():
            if shift_id in night_shift_ids:
                night_assignment_variables[(employee_id, assignment_date)].append(variable)

        employee_ids = sorted({employee_id for employee_id, *_ in ctx.assignment_variables})
        planning_dates = self._planning_dates(ctx)

        # Map (employee, date) to a boolean "worked_night" variable
        night_worked_variables: dict[tuple[int, date], cp_model.IntVar] = {}

        for employee_id in employee_ids:
            for planning_date in planning_dates:
                assignment_vars = night_assignment_variables[(employee_id, planning_date)]
                night_worked_variables[(employee_id, planning_date)] = self._get_worked_variable(
                    ctx,
                    assignment_vars,
                    name=f"mcns_night_e{employee_id}_d{planning_date}",
                )

        penalties: list[Penalty] = []

        # Process windows for each phase length
        for phase_length in self.PHASE_LENGTHS:
            if len(planning_dates) < phase_length:
                continue

            phase_variables: list[cp_model.IntVar] = []
            number_of_windows = len(planning_dates) - phase_length + 1

            for employee_id in employee_ids:
                for start_index in range(number_of_windows):
                    window_dates = planning_dates[start_index : start_index + phase_length]
                    per_day_variables = [
                        night_worked_variables[(employee_id, window_date)] for window_date in window_dates
                    ]

                    phase_variable = ctx.model.new_bool_var(
                        f"mcns_phase_e{employee_id}_d{window_dates[0]}_l{phase_length}"
                    )

                    # Native Boolean AND formulation
                    ctx.model.add_bool_and(per_day_variables).only_enforce_if(phase_variable)  # pyright: ignore[reportUnknownMemberType]
                    ctx.model.add_bool_or([v.Not() for v in per_day_variables]).only_enforce_if(phase_variable.Not())  # pyright: ignore[reportUnknownMemberType]

                    phase_variables.append(phase_variable)

            if phase_variables:
                penalties.append(
                    Penalty(
                        objective_id=self.id,
                        name=f"total_l{phase_length}",
                        expression=cp_model.LinearExpr.sum(phase_variables),  # pyright: ignore[reportUnknownMemberType]
                        multiplier=phase_length,
                    )
                )

        return tuple(penalties)

    @staticmethod
    def _get_worked_variable(ctx: SolverContext, variables: Sequence[cp_model.IntVar], *, name: str) -> cp_model.IntVar:
        worked = ctx.model.new_bool_var(name)
        if variables:
            ctx.model.add_max_equality(worked, list(variables))
        else:
            ctx.model.add(worked == 0)
        return worked

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
