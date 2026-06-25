import logging

from scheduling.domain import Assignment, AssignmentType
from scheduling.solver.models import Solution, SolutionStatus

logger = logging.getLogger(__name__)


class TimeOfficeSolutionWriter:
    """Allowed TimeOffice write surface for solver-generated assignments."""

    def write_dry_run(self, solution: Solution) -> None:
        if solution.status not in {SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE}:
            logger.info(
                "Skipping TimeOffice writeback dry-run because solution is not feasible: status=%s",
                solution.status.value,
            )
            return

        generated_assignments = _generated_assignments(solution)

        logger.info(
            "Running TimeOffice writeback dry-run: generated_assignments=%s",
            len(generated_assignments),
        )

        for assignment in generated_assignments:
            logger.debug(
                "Generated assignment for TimeOffice writeback dry-run: "
                "employee_id=%s planning_unit_id=%s date=%s shift_id=%s",
                assignment.employee_id,
                assignment.planning_unit_id,
                assignment.date.isoformat(),
                assignment.shift_id,
            )

        logger.info(
            "Finished TimeOffice writeback dry-run: generated_assignments=%s written=0",
            len(generated_assignments),
        )


def _generated_assignments(solution: Solution) -> tuple[Assignment, ...]:
    return tuple(
        assignment for assignment in solution.assignments if assignment.assignment_type == AssignmentType.GENERATED
    )
