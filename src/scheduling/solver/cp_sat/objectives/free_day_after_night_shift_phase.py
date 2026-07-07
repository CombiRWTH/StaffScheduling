from collections import defaultdict
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.domain.shift import ShiftType
from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class FreeDaysAfterNightShiftPhase:
    """
    Penalizes the pattern: night shift on day D, free on D+1, but working on D+2.
    The goal is to encourage two full consecutive rest days after a night shift.
    """

    id: ClassVar[str] = "free_days_after_night_shift_phase"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        night_shift_ids = {s.shift_id for s in ctx.dataset.shifts if s.type == ShiftType.NIGHT}
        if not night_shift_ids:
            return ()

        vars_by_employee_date: defaultdict[tuple[int, date], list[cp_model.IntVar]] = defaultdict(list)
        night_vars_by_employee_date: defaultdict[tuple[int, date], list[cp_model.IntVar]] = defaultdict(list)

        for (employee_id, _unit, d, shift_id, _level), var in ctx.assignment_variables.items():
            vars_by_employee_date[(employee_id, d)].append(var)
            if shift_id in night_shift_ids:
                night_vars_by_employee_date[(employee_id, d)].append(var)

        # Use the actual set of planning dates to avoid gaps when checking day+1 and day+2
        planning_dates = sorted({key[2] for key in ctx.assignment_variables})
        planning_dates_set = set(planning_dates)
        employee_ids = {key[0] for key in ctx.assignment_variables}
        penalties: list[cp_model.IntVar] = []

        for employee_id in employee_ids:
            for day in planning_dates:
                next_day = day + timedelta(days=1)
                after_next = day + timedelta(days=2)

                # Only proceed if both following days exist in the planning period
                if next_day not in planning_dates_set or after_next not in planning_dates_set:
                    continue

                night_vars = night_vars_by_employee_date[(employee_id, day)]
                if not night_vars:
                    continue

                # worked_night: employee worked a night shift on this day
                worked_night = ctx.model.new_bool_var(f"fdansp_night_e{employee_id}_d{day}")
                ctx.model.add(sum(night_vars) >= 1).only_enforce_if(worked_night)
                ctx.model.add(sum(night_vars) == 0).only_enforce_if(worked_night.Not())

                next_vars = vars_by_employee_date[(employee_id, next_day)]
                after_vars = vars_by_employee_date[(employee_id, after_next)]

                # next_free: employee has no assignment the day after the night shift
                next_free = ctx.model.new_bool_var(f"fdansp_next_free_e{employee_id}_d{day}")
                if next_vars:
                    ctx.model.add(sum(next_vars) == 0).only_enforce_if(next_free)
                    ctx.model.add(sum(next_vars) >= 1).only_enforce_if(next_free.Not())
                else:
                    ctx.model.add(next_free == 1)

                # after_worked: employee works two days after the night shift
                after_worked = ctx.model.new_bool_var(f"fdansp_after_worked_e{employee_id}_d{day}")
                if after_vars:
                    ctx.model.add(sum(after_vars) >= 1).only_enforce_if(after_worked)
                    ctx.model.add(sum(after_vars) == 0).only_enforce_if(after_worked.Not())
                else:
                    ctx.model.add(after_worked == 0)

                # Penalty fires when: night on D, free on D+1, but working on D+2
                penalty_var = ctx.model.new_bool_var(f"fdansp_penalty_e{employee_id}_d{day}")
                ctx.model.add(penalty_var == 1).only_enforce_if([worked_night, next_free, after_worked])
                ctx.model.add(penalty_var == 0).only_enforce_if(worked_night.Not())
                ctx.model.add(penalty_var == 0).only_enforce_if(next_free.Not())
                ctx.model.add(penalty_var == 0).only_enforce_if(after_worked.Not())
                penalties.append(penalty_var)

        if not penalties:
            return ()

        total = ctx.model.new_int_var(0, len(penalties), "fdansp_total")
        ctx.model.add(total == sum(penalties))
        return (Penalty(objective_id=self.id, name="total", expression=total),)

    def audit(self, ctx: AuditContext, params: Mapping[str, Any]) -> tuple[AuditFinding, ...]:
        return ()