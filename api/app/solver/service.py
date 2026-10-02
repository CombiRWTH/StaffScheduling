import logging
from time import monotonic
from typing import Literal

from ortools.sat.python import cp_model

from app.domain import POLICY, SchedulingDataset, check_schedule
from app.settings import Settings
from app.solver.diagnostics import DiagnosticSeverity, SolverDiagnostic
from app.solver.model import ScheduleModel, build_model
from app.solver.models import FOUND, RunConfiguration, Solution, SolutionStatus, StageReport

logger = logging.getLogger(__name__)

STATUS = {
    cp_model.OPTIMAL: SolutionStatus.OPTIMAL,
    cp_model.FEASIBLE: SolutionStatus.FEASIBLE,
    cp_model.INFEASIBLE: SolutionStatus.INFEASIBLE,
    cp_model.MODEL_INVALID: SolutionStatus.MODEL_INVALID,
}


class SolverService:
    """Solve one month lexicographically and check the schedule found.

    Each objective tier is one stage in priority order: it optimizes the tier within its share of
    the time, then fixes the value it reached and hands its schedule to the next stage as a hint.
    No lower tier can therefore buy back a unit of a higher one. Only the first stage can fail to
    find a schedule; a later stage that finds nothing better keeps the previous schedule. The
    solution keeps CP-SAT's status apart from the independent schedule check of the final schedule.
    Build errors raise; the generation job reports them as failed.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def solve(self, dataset: SchedulingDataset, timeout: float | None = None) -> Solution:
        built = build_model(dataset)
        configuration = RunConfiguration(
            policy=POLICY,
            timeout_seconds=timeout if timeout is not None else self._settings.solver_max_time_seconds,
            search_workers=self._settings.solver_num_search_workers,
            random_seed=self._settings.solver_random_seed,
        )
        logger.info(
            "Solving month=%s-%02d employees=%s candidates=%s stages=%s configuration=%s",
            dataset.planning_month.year,
            dataset.planning_month.month,
            len(dataset.employees),
            len(built.candidates),
            [tier.name for tier, _ in built.tiers],
            configuration.model_dump(mode="json", exclude={"policy"}),
        )
        if error := built.model.validate():
            invalid = SolverDiagnostic(code="cp_sat.model_invalid", severity=DiagnosticSeverity.ERROR, message=error)
            return Solution(
                status=SolutionStatus.MODEL_INVALID,
                configuration=configuration,
                wall_time_seconds=0,
                diagnostics=(*built.diagnostics, invalid),
            )
        started = monotonic()
        status, solver, stages = self._solve_stages(built, configuration)
        assignments = built.schedule(solver) if solver else ()
        gaps = built.declared_gaps(solver) if solver else ()
        solution = Solution(
            status=status,
            configuration=configuration,
            wall_time_seconds=monotonic() - started,
            assignments=assignments,
            gaps=gaps,
            stages=stages,
            check=check_schedule(dataset, assignments, gaps) if solver else None,
            diagnostics=built.diagnostics,
        )
        logger.info(
            "Solved status=%s assignments=%s gaps=%s stages=%s check=%s wall_time_seconds=%.3f",
            status.value,
            len(solution.assignments),
            sum(gap.missing_count for gap in gaps),
            [(stage.name, stage.status.value, stage.value) for stage in stages],
            solution.check.status.value if solution.check else None,
            solution.wall_time_seconds,
        )
        return solution

    def _solve_stages(
        self, built: ScheduleModel, configuration: RunConfiguration
    ) -> tuple[SolutionStatus, cp_model.CpSolver | None, tuple[StageReport, ...]]:
        """The overall status, the solver holding the final schedule (None without one) and every stage."""
        deadline = monotonic() + configuration.timeout_seconds
        model = built.model
        best: cp_model.CpSolver | None = None
        # Each stage's status and proven bound; its value is read from the final schedule, which a
        # later stage may still improve within the fixed limit when this stage was only feasible.
        proven: list[tuple[Literal[SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE], float]] = []
        for index, (tier, expr) in enumerate(built.tiers):
            if tier.reward:
                model.maximize(expr)
            else:
                model.minimize(expr)
            solver = self._solver(configuration, (deadline - monotonic()) / (len(built.tiers) - index))
            status = STATUS.get(solver.solve(model), SolutionStatus.UNKNOWN)
            if status in FOUND:
                best = solver
            elif best is None:
                return status, None, ()
            # Without a schedule in the stage's time, the previous one stands, unproven for this tier.
            optimal = SolutionStatus.OPTIMAL if status == SolutionStatus.OPTIMAL else SolutionStatus.FEASIBLE
            proven.append((optimal, solver.best_objective_bound))
            value = best.value(expr)
            model.add(expr >= value if tier.reward else expr <= value)
            model.clear_hints()
            for variable in built.candidates.values():
                model.add_hint(variable, best.value(variable))
        if best is None:
            raise RuntimeError("OBJECTIVES has no tier to solve.")
        stages = tuple(
            StageReport(name=tier.name, status=status, value=int(best.value(expr)), best_bound=bound)
            for (tier, expr), (status, bound) in zip(built.tiers, proven, strict=True)
        )
        optimal = all(status == SolutionStatus.OPTIMAL for status, _ in proven)
        return SolutionStatus.OPTIMAL if optimal else SolutionStatus.FEASIBLE, best, stages

    def _solver(self, configuration: RunConfiguration, seconds: float) -> cp_model.CpSolver:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max(seconds, 0.0)
        solver.parameters.log_search_progress = self._settings.solver_log_search_progress
        if configuration.search_workers is not None:
            solver.parameters.num_workers = configuration.search_workers
        if configuration.random_seed is not None:
            solver.parameters.random_seed = configuration.random_seed
        return solver
