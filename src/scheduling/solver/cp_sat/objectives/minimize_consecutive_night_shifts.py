from collections import defaultdict
from collections.abc import Mapping
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

    Each phase length produces a separate penalty. Longer phases receive a
    larger multiplier.

    A window variable is one exactly when the employee works a night shift on
    every calendar day in that window.
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

        employee_ids = sorted(
            {employee_id for employee_id, _planning_unit_id, _date, _shift_id, _level in ctx.assignment_variables}
        )

        planning_dates = self._planning_dates(ctx)

        night_worked_variables: dict[
            tuple[int, date],
            cp_model.IntVar,
        ] = {}

        for employee_id in employee_ids:
            for planning_date in planning_dates:
                assignment_variables = night_assignment_variables[(employee_id, planning_date)]

                night_worked = ctx.model.new_bool_var(f"mcns_night_e{employee_id}_d{planning_date}")

                if assignment_variables:
                    ctx.model.add_max_equality(
                        night_worked,
                        assignment_variables,
                    )
                else:
                    ctx.model.add(night_worked == 0)

                night_worked_variables[(employee_id, planning_date)] = night_worked

        penalties: list[Penalty] = []

        for phase_length in self.PHASE_LENGTHS:
            phase_variables: list[cp_model.IntVar] = []

            for employee_id in employee_ids:
                number_of_windows = len(planning_dates) - phase_length + 1

                for start_index in range(number_of_windows):
                    window_dates = planning_dates[start_index : start_index + phase_length]

                    per_day_variables = [
                        night_worked_variables[(employee_id, window_date)] for window_date in window_dates
                    ]

                    phase_variable = ctx.model.new_bool_var(
                        f"mcns_phase_e{employee_id}_d{window_dates[0]}_l{phase_length}"
                    )

                    # For Boolean variables, their minimum is one exactly when
                    # every variable is one.
                    ctx.model.add_min_equality(
                        phase_variable,
                        per_day_variables,
                    )

                    phase_variables.append(phase_variable)

            if not phase_variables:
                continue

            total = ctx.model.new_int_var(
                0,
                len(phase_variables),
                f"mcns_total_l{phase_length}",
            )
            ctx.model.add(total == sum(phase_variables))

            penalties.append(
                Penalty(
                    objective_id=self.id,
                    name=f"total_l{phase_length}",
                    expression=total,
                    multiplier=phase_length,
                )
            )

        return tuple(penalties)

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
