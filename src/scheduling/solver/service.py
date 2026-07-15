import logging

from ortools.sat.python import cp_model

from scheduling.domain import Assignment, AssignmentType, SchedulingDataset
from scheduling.settings import Settings
from scheduling.solver.audit import AuditFinding, AuditReport
from scheduling.solver.cp_sat.builder import CpSatBuildResult, CpSatModelBuilder
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.inspection import CpSatInspection, inspect_cp_sat_model
from scheduling.solver.diagnostics import DiagnosticSeverity, SolverDiagnostic
from scheduling.solver.models import Solution, SolutionStatus

logger = logging.getLogger(__name__)


class SolverService:
    """Build, solve, map, audit, and report CP-SAT scheduling solutions."""

    def __init__(self, settings: Settings, model_builder: CpSatModelBuilder) -> None:
        self._settings = settings
        self._model_builder = model_builder

    def solve(self, dataset: SchedulingDataset) -> Solution:
        build_result = self._build_model(dataset)
        ctx = build_result.ctx

        inspection = self._inspect_model(ctx)

        if not inspection.is_valid:
            return Solution(
                status=SolutionStatus.MODEL_INVALID,
                assignments=(),
                diagnostics=tuple(ctx.diagnostics),
                audit=AuditReport(),
            )

        solver = self._create_solver()

        logger.info(
            "Solving CP-SAT model: max_time_seconds=%s search_workers=%s random_seed=%s",
            self._settings.solver_max_time_seconds,
            self._settings.solver_num_search_workers,
            self._settings.solver_random_seed,
        )

        cp_status = solver.solve(ctx.model)
        status = self._map_cp_sat_status(cp_status)

        assignments = (
            self._extract_assignments(ctx=ctx, solver=solver)
            if status in {SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE}
            else ()
        )

        audit = (
            self._audit_solution(
                build_result=build_result,
                dataset=dataset,
                assignments=assignments,
            )
            if status in {SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE}
            else AuditReport()
        )

        self._log_solve_result(
            status=status,
            assignment_count=len(assignments),
            diagnostic_count=len(ctx.diagnostics),
            audit_finding_count=len(audit.findings),
            solver=solver,
        )

        if ctx.diagnostics:
            logger.debug(
                "Solver diagnostics: diagnostics=%s",
                tuple(diagnostic.message for diagnostic in ctx.diagnostics),
            )

        return Solution(
            status=status,
            assignments=assignments,
            diagnostics=tuple(ctx.diagnostics),
            audit=audit,
        )

    def _build_model(self, dataset: SchedulingDataset) -> CpSatBuildResult:
        logger.info(
            "Building CP-SAT model: employees=%s planning_units=%s shifts=%s "
            "existing_assignments=%s demand_requirements=%s",
            len(dataset.employees),
            len(dataset.planning_units),
            len(dataset.shifts),
            len(dataset.assignments),
            len(dataset.demand_requirements),
        )

        build_result = self._model_builder.build(dataset)

        logger.debug(
            "Applied solver components: constraints=%s objectives=%s weighted_penalties=%s has_objective=%s",
            build_result.applied_constraint_ids,
            build_result.applied_objective_ids,
            build_result.weighted_penalty_count,
            build_result.has_objective,
        )

        return build_result

    def _inspect_model(self, ctx: SolverContext) -> CpSatInspection:
        inspection = inspect_cp_sat_model(model=ctx.model)

        logger.info(
            "Built CP-SAT model: assignment_variables=%s proto_variables=%s "
            "proto_constraints=%s constraint_types=%s diagnostics=%s",
            len(ctx.assignment_variables),
            inspection.proto_variable_count,
            inspection.proto_constraint_count,
            inspection.constraint_type_counts,
            len(ctx.diagnostics),
        )

        if inspection.unnamed_constraint_count:
            logger.warning(
                "CP-SAT model contains unnamed constraints: unnamed_constraints=%s",
                inspection.unnamed_constraint_count,
            )

        if not inspection.is_valid:
            logger.error("CP-SAT model validation failed: %s", inspection.validation_error)
            ctx.diagnostics.append(
                SolverDiagnostic(
                    code="cp_sat.model_invalid",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"CP-SAT model validation failed: {inspection.validation_error}",
                )
            )

        logger.debug("CP-SAT constraint names: names=%s", inspection.constraint_names)

        return inspection

    def _create_solver(self) -> cp_model.CpSolver:
        solver = cp_model.CpSolver()

        solver.parameters.max_time_in_seconds = self._settings.solver_max_time_seconds
        solver.parameters.log_search_progress = self._settings.solver_log_search_progress

        if self._settings.solver_num_search_workers is not None:
            solver.parameters.num_search_workers = self._settings.solver_num_search_workers

        if self._settings.solver_random_seed is not None:
            solver.parameters.random_seed = self._settings.solver_random_seed

        return solver

    def _map_cp_sat_status(self, status: cp_model.CpSolverStatus) -> SolutionStatus:
        if status == cp_model.OPTIMAL:
            return SolutionStatus.OPTIMAL

        if status == cp_model.FEASIBLE:
            return SolutionStatus.FEASIBLE

        if status == cp_model.INFEASIBLE:
            return SolutionStatus.INFEASIBLE

        if status == cp_model.MODEL_INVALID:
            return SolutionStatus.MODEL_INVALID

        return SolutionStatus.UNKNOWN

    def _extract_assignments(
        self,
        *,
        ctx: SolverContext,
        solver: cp_model.CpSolver,
    ) -> tuple[Assignment, ...]:
        assignments: list[Assignment] = []

        for key, variable in ctx.assignment_variables.items():
            if solver.value(variable) != 1:
                continue

            employee_id, planning_unit_id, assignment_date, shift_id, _ = key

            assignments.append(
                Assignment(
                    employee_id=employee_id,
                    planning_unit_id=planning_unit_id,
                    date=assignment_date,
                    shift_id=shift_id,
                    assignment_type=AssignmentType.GENERATED,
                )
            )

        return tuple(
            sorted(
                assignments,
                key=lambda assignment: (
                    assignment.planning_unit_id,
                    assignment.date,
                    assignment.shift_id,
                    assignment.employee_id,
                ),
            )
        )

    def _audit_solution(
        self,
        *,
        build_result: CpSatBuildResult,
        dataset: SchedulingDataset,
        assignments: tuple[Assignment, ...],
    ) -> AuditReport:
        # add the already existing assignments to the ones generated by the solver
        all_assignments = assignments + tuple(dataset.assignments)

        audit_ctx = AuditContext(dataset=dataset, index=build_result.ctx.index, assignments=all_assignments)

        findings: list[AuditFinding] = []

        for resolved in build_result.constraints:
            if not resolved.enabled:
                continue

            findings.extend(
                resolved.constraint.audit(
                    audit_ctx,
                    params=resolved.params,
                )
            )

        for resolved in build_result.objectives:
            if not resolved.enabled:
                continue

            findings.extend(
                resolved.objective.audit(
                    audit_ctx,
                    params=resolved.params,
                )
            )

        return AuditReport(findings=tuple(findings))

    def _log_solve_result(
        self,
        *,
        status: SolutionStatus,
        assignment_count: int,
        diagnostic_count: int,
        audit_finding_count: int,
        solver: cp_model.CpSolver,
    ) -> None:
        message = (
            "Solved CP-SAT model: status=%s generated_assignments=%s diagnostics=%s "
            "audit_findings=%s wall_time_seconds=%.3f"
        )
        args = (
            status.value,
            assignment_count,
            diagnostic_count,
            audit_finding_count,
            solver.wall_time,
        )

        if status in {SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE}:
            logger.info(message, *args)
        elif status == SolutionStatus.MODEL_INVALID:
            logger.error(message, *args)
        else:
            logger.warning(message, *args)
