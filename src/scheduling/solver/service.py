import logging
from collections.abc import Callable

from ortools.sat.python import cp_model

from scheduling.domain import Assignment, AssignmentType, SchedulingDataset
from scheduling.settings import Settings
from scheduling.solver.cp_sat.constraints.employee_daily import add_one_assignment_per_employee_day_constraints
from scheduling.solver.cp_sat.constraints.minimum_staffing import add_minimum_staffing_constraints
from scheduling.solver.cp_sat.context import SolverContext, create_context
from scheduling.solver.cp_sat.objectives.balance_generated_assignments import (
    add_balance_generated_assignments_objective,
)
from scheduling.solver.cp_sat.variables import create_assignment_variables
from scheduling.solver.models import Solution, SolutionStatus

logger = logging.getLogger(__name__)

type ModelStepFunction = Callable[[SolverContext], None]


CONSTRAINTS: tuple[ModelStepFunction, ...] = (
    add_minimum_staffing_constraints,
    add_one_assignment_per_employee_day_constraints,
)

OBJECTIVES: tuple[ModelStepFunction, ...] = (add_balance_generated_assignments_objective,)


class SolverService:
    """Builds and solves the CP-SAT scheduling model."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def solve(self, dataset: SchedulingDataset) -> Solution:
        ctx = self._build_model(dataset)
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

        self._log_solve_result(
            status=status,
            assignment_count=len(assignments),
            diagnostic_count=len(ctx.diagnostics),
            solver=solver,
        )

        if ctx.diagnostics:
            logger.debug("Solver diagnostics: diagnostics=%s", tuple(ctx.diagnostics))

        return Solution(
            status=status,
            assignments=assignments,
            diagnostics=tuple(ctx.diagnostics),
        )

    def _build_model(self, dataset: SchedulingDataset) -> SolverContext:
        logger.info(
            "Building CP-SAT model: employees=%s planning_units=%s shifts=%s "
            "existing_assignments=%s demand_requirements=%s",
            len(dataset.employees),
            len(dataset.planning_units),
            len(dataset.shifts),
            len(dataset.assignments),
            len(dataset.demand_requirements),
        )

        ctx = create_context(dataset=dataset)

        create_assignment_variables(ctx)

        for add_constraint in CONSTRAINTS:
            logger.debug("Applying solver constraint: name=%s", add_constraint.__name__)
            add_constraint(ctx)

        for add_objective in OBJECTIVES:
            logger.debug("Applying solver objective: name=%s", add_objective.__name__)
            add_objective(ctx)

        if ctx.objective_terms:
            objective = sum(term.weight * term.expression for term in ctx.objective_terms)
            ctx.model.minimize(objective)
        else:
            logger.debug("No solver objective terms registered.")

        logger.info(
            "Built CP-SAT model: variables=%s constraints=%s objective_terms=%s diagnostics=%s",
            len(ctx.assignment_variables),
            len(CONSTRAINTS),
            tuple(term.name for term in ctx.objective_terms),
            len(ctx.diagnostics),
        )

        return ctx

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

    def _log_solve_result(
        self,
        *,
        status: SolutionStatus,
        assignment_count: int,
        diagnostic_count: int,
        solver: cp_model.CpSolver,
    ) -> None:
        message = "Solved CP-SAT model: status=%s generated_assignments=%s diagnostics=%s wall_time_seconds=%.3f"
        args = (
            status.value,
            assignment_count,
            diagnostic_count,
            solver.wall_time,
        )

        if status in {SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE}:
            logger.info(message, *args)
        elif status == SolutionStatus.MODEL_INVALID:
            logger.error(message, *args)
        else:
            logger.warning(message, *args)
