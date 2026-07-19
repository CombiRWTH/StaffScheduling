from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.domain.shift import ShiftType
from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty

type EmployeeDateKey = tuple[int, date]


class FreeDaysAfterNightShiftPhase:
    """Encourage two consecutive free days after a night-shift phase.

    A penalty is generated for this pattern:

        night on D
        free on D + 1
        worked on D + 2

    The hard constraint already guarantees one free day after a night-shift
    phase. This objective encourages extending that recovery period to two days.
    """

    id: ClassVar[str] = "free_days_after_night_shift_phase"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        del params

        if not ctx.assignment_variables:
            return ()

        night_shift_ids = {shift.shift_id for shift in ctx.dataset.shifts if shift.type == ShiftType.NIGHT}

        if not night_shift_ids:
            return ()

        variables_by_employee_date: defaultdict[
            EmployeeDateKey,
            list[cp_model.IntVar],
        ] = defaultdict(list)

        night_variables_by_employee_date: defaultdict[
            EmployeeDateKey,
            list[cp_model.IntVar],
        ] = defaultdict(list)

        for (
            employee_id,
            _planning_unit_id,
            assignment_date,
            shift_id,
            _staff_level,
        ), variable in ctx.assignment_variables.items():
            variables_by_employee_date[(employee_id, assignment_date)].append(variable)

            if shift_id in night_shift_ids:
                night_variables_by_employee_date[(employee_id, assignment_date)].append(variable)

        planning_dates = self._planning_dates(ctx)
        planning_date_set = set(planning_dates)

        employee_ids = sorted(
            {
                employee_id
                for (
                    employee_id,
                    _planning_unit_id,
                    _assignment_date,
                    _shift_id,
                    _staff_level,
                ) in ctx.assignment_variables
            }
        )

        penalties: list[cp_model.IntVar] = []

        for employee_id in employee_ids:
            for current_date in planning_dates:
                next_date = current_date + timedelta(days=1)
                second_next_date = current_date + timedelta(days=2)

                if next_date not in planning_date_set or second_next_date not in planning_date_set:
                    continue

                night_variables = night_variables_by_employee_date.get(
                    (employee_id, current_date),
                    [],
                )

                if not night_variables:
                    continue

                worked_night = self._worked_variable(
                    ctx,
                    night_variables,
                    name=(f"fdansp__night_e{employee_id}__d{current_date}"),
                )

                worked_next_day = self._worked_or_zero(
                    ctx,
                    variables_by_employee_date.get(
                        (employee_id, next_date),
                        [],
                    ),
                    name=(f"fdansp__worked_next_e{employee_id}__d{current_date}"),
                )

                next_day_free = ctx.model.new_bool_var(f"fdansp__next_free_e{employee_id}__d{current_date}")
                ctx.model.add(next_day_free + worked_next_day == 1)

                worked_second_next_day = self._worked_or_zero(
                    ctx,
                    variables_by_employee_date.get(
                        (employee_id, second_next_date),
                        [],
                    ),
                    name=(f"fdansp__worked_second_next_e{employee_id}__d{current_date}"),
                )

                penalty = ctx.model.new_bool_var(f"fdansp__penalty_e{employee_id}__d{current_date}")

                # Boolean minimum is logical AND.
                ctx.model.add_min_equality(
                    penalty,
                    [
                        worked_night,
                        next_day_free,
                        worked_second_next_day,
                    ],
                )

                penalties.append(penalty)

        if not penalties:
            return ()

        total = ctx.model.new_int_var(
            0,
            len(penalties),
            "fdansp__total",
        )
        ctx.model.add(total == sum(penalties))

        return (
            Penalty(
                objective_id=self.id,
                name="total",
                expression=total,
            ),
        )

    @staticmethod
    def _worked_variable(ctx: SolverContext, variables: Sequence[cp_model.IntVar], *, name: str) -> cp_model.IntVar:
        worked = ctx.model.new_bool_var(name)
        ctx.model.add_max_equality(worked, list(variables))
        return worked

    @classmethod
    def _worked_or_zero(cls, ctx: SolverContext, variables: Sequence[cp_model.IntVar], *, name: str) -> cp_model.IntVar:
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
