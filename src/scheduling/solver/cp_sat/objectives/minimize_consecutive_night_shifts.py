from collections import defaultdict
from collections.abc import Mapping
from datetime import date
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.domain.shift import ShiftType
from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class MinimizeConsecutiveNightShifts:
    """
    Penalizes windows of consecutive night shifts of length 2, 3, and 4.
    Each phase length produces a separate Penalty with multiplier=phase_length,
    so longer phases are penalized more heavily by the model builder.

    For each window: a bool variable is True iff the employee worked a night
    shift on every day in the window. If an employee can work multiple night
    shift types, a per-day aggregation bool is created first.
    """

    id: ClassVar[str] = "minimize_consecutive_night_shifts"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        night_shift_ids = {s.shift_id for s in ctx.dataset.shifts if s.type == ShiftType.NIGHT}
        if not night_shift_ids:
            return ()

        night_vars_by_employee_date: defaultdict[tuple[int, date], list[cp_model.IntVar]] = defaultdict(list)
        for (employee_id, _unit, d, shift_id, _level), var in ctx.assignment_variables.items():
            if shift_id in night_shift_ids:
                night_vars_by_employee_date[(employee_id, d)].append(var)

        planning_dates = sorted({key[2] for key in ctx.assignment_variables})
        employee_ids = {key[0] for key in ctx.assignment_variables}
        result: list[Penalty] = []

        for phase_length in (2, 3, 4):
            phase_vars: list[cp_model.IntVar] = []

            for employee_id in employee_ids:
                for i, day in enumerate(planning_dates[: -(phase_length - 1)]):
                    window_days = [planning_dates[i + offset] for offset in range(phase_length)]

                    # Build one bool per day in the window indicating a night shift was worked.
                    # If there is only one night shift type, reuse its variable directly.
                    per_day: list[cp_model.IntVar] = []
                    for wd in window_days:
                        day_night_vars = night_vars_by_employee_date[(employee_id, wd)]
                        if not day_night_vars:
                            # No night shift possible on this day; window can never be active
                            break
                        if len(day_night_vars) == 1:
                            per_day.append(day_night_vars[0])
                        else:
                            # Aggregate multiple night shift variables into one bool
                            b = ctx.model.new_bool_var(f"mcns_night_e{employee_id}_d{wd}_l{phase_length}")
                            ctx.model.add(sum(day_night_vars) >= 1).only_enforce_if(b)
                            ctx.model.add(sum(day_night_vars) == 0).only_enforce_if(b.Not())
                            per_day.append(b)
                    else:
                        # for/else: only reached if no break occurred (all days have night vars)
                        phase_var = ctx.model.new_bool_var(f"mcns_phase_e{employee_id}_d{day}_l{phase_length}")
                        ctx.model.add_bool_and(per_day).only_enforce_if(phase_var)
                        ctx.model.add_bool_or([v.Not() for v in per_day]).only_enforce_if(phase_var.Not())
                        phase_vars.append(phase_var)

            if phase_vars:
                total = ctx.model.new_int_var(0, len(phase_vars), f"mcns_total_l{phase_length}")
                ctx.model.add(total == sum(phase_vars))
                result.append(
                    Penalty(
                        objective_id=self.id,
                        name=f"total_l{phase_length}",
                        expression=total,
                        multiplier=phase_length,  # longer phases cost more
                    )
                )

        return tuple(result)

    def audit(self, ctx: AuditContext, params: Mapping[str, Any]) -> tuple[AuditFinding, ...]:
        return ()
