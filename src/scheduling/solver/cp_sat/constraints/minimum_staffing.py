from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.keys import AssignmentVariableKey, DemandKey
from scheduling.solver.diagnostics import DiagnosticSeverity, SolverDiagnostic


class MinimumStaffing:
    """Cover minimum staffing requirements from SchedulingDataset demand.

    Demand describes the absolute minimum. Overstaffing is intentionally allowed.
    """

    id: ClassVar[str] = "minimum_staffing"
    required: ClassVar[bool] = True

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]:
        del params
        diagnostics: list[SolverDiagnostic] = []
        vars_by_demand = _group_vars_by_demand(ctx)

        for demand_key, required_count in ctx.index.required_count_by_demand_key.items():
            variables = vars_by_demand.get(demand_key, [])

            if len(variables) < required_count:
                diagnostics.append(
                    _not_enough_candidates_diagnostic(
                        demand_key=demand_key,
                        required_count=required_count,
                        candidate_count=len(variables),
                    )
                )

            ctx.model.add(sum(variables) >= required_count).with_name(_minimum_staffing_constraint_name(demand_key))

        return tuple(diagnostics)

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        del params

        findings: list[AuditFinding] = []
        actual_by_demand = _count_actual_assignments_by_demand(ctx)

        for demand_key, required_count in ctx.index.required_count_by_demand_key.items():
            actual_count = actual_by_demand.get(demand_key, 0)

            if actual_count >= required_count:
                continue

            planning_unit_id, demand_date, shift_id, staff_level = demand_key
            findings.append(
                AuditFinding(
                    code="minimum_staffing.uncovered",
                    severity=AuditSeverity.ERROR,
                    source_id=self.id,
                    message=(
                        "Minimum staffing demand is not covered "
                        f"required_count={required_count} actual_count={actual_count}."
                    ),
                    planning_unit_id=planning_unit_id,
                    date=demand_date,
                    shift_id=shift_id,
                    staff_level=staff_level.value,
                )
            )

        return tuple(findings)


def _minimum_staffing_constraint_name(demand_key: DemandKey) -> str:
    planning_unit_id, demand_date, shift_id, staff_level = demand_key

    return (
        "minimum_staffing"
        f"__unit_{planning_unit_id}"
        f"__date_{demand_date:%Y%m%d}"
        f"__shift_{shift_id}"
        f"__level_{staff_level.value}"
    )


def _group_vars_by_demand(
    ctx: SolverContext,
) -> dict[DemandKey, list[cp_model.IntVar]]:
    grouped: defaultdict[DemandKey, list[cp_model.IntVar]] = defaultdict(list)

    for key, variable in ctx.assignment_variables.items():
        grouped[_demand_key_from_assignment_key(key)].append(variable)

    return dict(grouped)


def _demand_key_from_assignment_key(key: AssignmentVariableKey) -> DemandKey:
    _, planning_unit_id, assignment_date, shift_id, staff_level = key
    return planning_unit_id, assignment_date, shift_id, staff_level


def _not_enough_candidates_diagnostic(
    *,
    demand_key: DemandKey,
    required_count: int,
    candidate_count: int,
) -> SolverDiagnostic:
    planning_unit_id, demand_date, shift_id, staff_level = demand_key

    return SolverDiagnostic(
        code="minimum_staffing.not_enough_candidates",
        severity=DiagnosticSeverity.ERROR,
        message=(
            "Minimum staffing demand has too few eligible candidates "
            f"planning_unit_id={planning_unit_id} "
            f"date={demand_date.isoformat()} "
            f"shift_id={shift_id} "
            f"staff_level={staff_level.value} "
            f"required_count={required_count} "
            f"candidate_count={candidate_count}."
        ),
    )


def _count_actual_assignments_by_demand(ctx: AuditContext) -> dict[DemandKey, int]:
    actual: defaultdict[DemandKey, int] = defaultdict(int)

    for assignment in ctx.assignments:
        if assignment.planning_unit_id is None:
            continue

        employee = ctx.index.employees_by_id.get(assignment.employee_id)
        if employee is None:
            continue

        key = (
            assignment.planning_unit_id,
            assignment.date,
            assignment.shift_id,
            employee.staff_level,
        )
        actual[key] += 1

    return dict(actual)
