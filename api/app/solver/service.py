import logging

from ortools.sat.python import cp_model

from app.domain import POLICY, SchedulingDataset, check_schedule
from app.settings import Settings
from app.solver.diagnostics import DiagnosticSeverity, SolverDiagnostic
from app.solver.model import build_model
from app.solver.models import FOUND, ObjectiveReport, RunConfiguration, Solution, SolutionStatus

logger = logging.getLogger(__name__)

STATUS = {
    cp_model.OPTIMAL: SolutionStatus.OPTIMAL,
    cp_model.FEASIBLE: SolutionStatus.FEASIBLE,
    cp_model.INFEASIBLE: SolutionStatus.INFEASIBLE,
    cp_model.MODEL_INVALID: SolutionStatus.MODEL_INVALID,
}


class SolverService:
    """Solve one month and check the schedule found.

    The solution keeps CP-SAT's status apart from the independent schedule check, which runs on
    every candidate schedule. Build errors raise; the generation job reports them as failed.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def solve(self, dataset: SchedulingDataset, timeout: float | None = None) -> Solution:
        built = build_model(dataset)
        configuration = RunConfiguration(
            policy=POLICY,
            weights=built.weights,
            timeout_seconds=timeout if timeout is not None else self._settings.solver_max_time_seconds,
            search_workers=self._settings.solver_num_search_workers,
            random_seed=self._settings.solver_random_seed,
        )
        logger.info(
            "Solving month=%s-%02d employees=%s candidates=%s configuration=%s",
            dataset.planning_month.year,
            dataset.planning_month.month,
            len(dataset.employees),
            len(built.candidates),
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
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = configuration.timeout_seconds
        solver.parameters.log_search_progress = self._settings.solver_log_search_progress
        if configuration.search_workers is not None:
            solver.parameters.num_workers = configuration.search_workers
        if configuration.random_seed is not None:
            solver.parameters.random_seed = configuration.random_seed
        status = STATUS.get(solver.solve(built.model), SolutionStatus.UNKNOWN)
        found = status in FOUND
        assignments = built.schedule(solver) if found else ()
        solution = Solution(
            status=status,
            configuration=configuration,
            wall_time_seconds=solver.wall_time,
            assignments=assignments,
            objective=ObjectiveReport(value=round(solver.objective_value), best_bound=solver.best_objective_bound)
            if found
            else None,
            check=check_schedule(dataset, assignments) if found else None,
            diagnostics=built.diagnostics,
        )
        logger.info(
            "Solved status=%s assignments=%s check=%s wall_time_seconds=%.3f",
            status.value,
            len(solution.assignments),
            solution.check.status.value if solution.check else None,
            solver.wall_time,
        )
        return solution
