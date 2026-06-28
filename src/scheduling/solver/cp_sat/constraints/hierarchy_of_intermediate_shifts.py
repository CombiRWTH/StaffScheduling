import datetime
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.diagnostics import SolverDiagnostic


class HierarchyOfIntermediateShifts:
    """Enforce a strict hierarchy and even distribution for intermediate shifts.

    Per planning_unit and week: Mon-Fri must be filled before weekends are assigned.
    """

    id: ClassVar[str] = "hierarchy_of_intermediate_shifts"
    required: ClassVar[bool] = True

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]:
        del params

        vars_by_unit_week_day, active_unit_weeks = _group_vars(ctx)

        for planning_unit_id, (iso_year, iso_week) in active_unit_weeks:
            days_in_week = vars_by_unit_week_day[planning_unit_id][(iso_year, iso_week)]

            weekdays_exprs: list[cp_model.LinearExpr] = []
            weekends_exprs: list[cp_model.LinearExpr] = []

            for date, variables in days_in_week.items():
                day_sum = cp_model.LinearExpr.Sum(variables)  # type: ignore

                if date.isoweekday() in {6, 7}:
                    weekends_exprs.append(day_sum)
                else:
                    weekdays_exprs.append(day_sum)

            if weekdays_exprs and weekends_exprs:
                max_capacity = len(ctx.assignment_variables)

                max_wd = ctx.model.new_int_var(
                    0, max_capacity, f"max_wd_u:{planning_unit_id}_y:{iso_year}_w:{iso_week}"
                )
                min_wd = ctx.model.new_int_var(
                    0, max_capacity, f"min_wd_u:{planning_unit_id}_y:{iso_year}_w:{iso_week}"
                )
                max_we = ctx.model.new_int_var(
                    0, max_capacity, f"max_we_u:{planning_unit_id}_y:{iso_year}_w:{iso_week}"
                )
                min_we = ctx.model.new_int_var(
                    0, max_capacity, f"min_we_u:{planning_unit_id}_y:{iso_year}_w:{iso_week}"
                )

                ctx.model.add_max_equality(max_wd, weekdays_exprs)
                ctx.model.add_min_equality(min_wd, weekdays_exprs)
                ctx.model.add_max_equality(max_we, weekends_exprs)
                ctx.model.add_min_equality(min_we, weekends_exprs)

                constr_dist_wd = ctx.model.add(max_wd - min_wd <= 1)
                constr_dist_wd.with_name(f"hier_inter_dist_wd__unit_{planning_unit_id}__y_{iso_year}_w_{iso_week}")

                constr_dist_we = ctx.model.add(max_we - min_we <= 1)
                constr_dist_we.with_name(f"hier_inter_dist_we__unit_{planning_unit_id}__y_{iso_year}_w_{iso_week}")

                constr_step_a = ctx.model.add(max_wd <= min_we + 1)
                constr_step_a.with_name(f"hier_inter_step_a__unit_{planning_unit_id}__y_{iso_year}_w_{iso_week}")

                constr_step_b = ctx.model.add(min_wd >= max_we)
                constr_step_b.with_name(f"hier_inter_step_b__unit_{planning_unit_id}__y_{iso_year}_w_{iso_week}")

        return ()

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        del params

        findings: list[AuditFinding] = []
        counts_by_day, active_dates_by_unit = _group_actual_shifts(ctx)

        for planning_unit_id, active_dates in active_dates_by_unit.items():
            weeks: defaultdict[tuple[int, int], list[datetime.date]] = defaultdict(list)
            for date in active_dates:
                iso_year, iso_week = date.isocalendar()[:2]
                weeks[(iso_year, iso_week)].append(date)

            for (iso_year, iso_week), dates_in_week in weeks.items():
                wd_counts: list[int] = []
                we_counts: list[int] = []

                for date in dates_in_week:
                    count = counts_by_day.get((planning_unit_id, date), 0)

                    if date.isoweekday() in {6, 7}:
                        we_counts.append(count)
                    else:
                        wd_counts.append(count)

                if wd_counts and we_counts:
                    max_wd, min_wd = max(wd_counts), min(wd_counts)
                    max_we, min_we = max(we_counts), min(we_counts)

                    is_dist_invalid: bool = (max_wd - min_wd > 1) or (max_we - min_we > 1)
                    is_hier_invalid: bool = (max_wd > min_we + 1) or (min_wd < max_we)

                    if is_dist_invalid or is_hier_invalid:
                        findings.append(
                            AuditFinding(
                                code="hierarchy_of_intermediate_shifts.violation",
                                severity=AuditSeverity.ERROR,
                                source_id=self.id,
                                message=(
                                    f"Intermediate shifts hierarchy violated. "
                                    f"planning_unit_id={planning_unit_id} year={iso_year} week={iso_week} "
                                    f"max_wd={max_wd} min_wd={min_wd} max_we={max_we} min_we={min_we}."
                                ),
                                planning_unit_id=planning_unit_id,
                                date=dates_in_week[0],
                            )
                        )

        return tuple(findings)


# --- Helper Functions ---


def _is_intermediate_shift(ctx: SolverContext | AuditContext, shift_id: int) -> bool:
    if hasattr(ctx, "is_intermediate_shift"):
        return ctx.is_intermediate_shift(shift_id)  # type: ignore
    return False


def _group_vars(
    ctx: SolverContext,
) -> tuple[
    dict[int, dict[tuple[int, int], dict[datetime.date, list[cp_model.IntVar]]]], set[tuple[int, tuple[int, int]]]
]:
    grouped: defaultdict[int, defaultdict[tuple[int, int], defaultdict[datetime.date, list[cp_model.IntVar]]]] = (
        defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    )
    active_weeks: set[tuple[int, tuple[int, int]]] = set()

    for key, variable in ctx.assignment_variables.items():
        _, shift_id, assignment_date, planning_unit_id, _ = key

        if not _is_intermediate_shift(ctx, shift_id):
            continue

        iso_year, iso_week = assignment_date.isocalendar()[:2]
        grouped[planning_unit_id][(iso_year, iso_week)][assignment_date].append(variable)
        active_weeks.add((planning_unit_id, (iso_year, iso_week)))

    clean_grouped = {p_id: {week: dict(days) for week, days in weeks.items()} for p_id, weeks in grouped.items()}

    return clean_grouped, active_weeks


def _group_actual_shifts(
    ctx: AuditContext,
) -> tuple[dict[tuple[int, datetime.date], int], dict[int, set[datetime.date]]]:
    counts_by_day: defaultdict[tuple[int, datetime.date], int] = defaultdict(int)
    active_dates_by_unit: defaultdict[int, set[datetime.date]] = defaultdict(set)

    for assignment in ctx.assignments:
        if assignment.planning_unit_id is None:
            continue

        active_dates_by_unit[assignment.planning_unit_id].add(assignment.date)

        if _is_intermediate_shift(ctx, assignment.shift_id):
            counts_by_day[(assignment.planning_unit_id, assignment.date)] += 1

    return dict(counts_by_day), dict(active_dates_by_unit)
