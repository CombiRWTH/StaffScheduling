import logging

from scheduling.domain import AssignmentType, PlanningMonth
from scheduling.solver.models import Solution, SolutionStatus
from scheduling.timeoffice.database import TimeOfficeDatabase
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.validation.dataset import ValidatedSchedulingDataset

logger = logging.getLogger(__name__)


class TimeOfficeService:
    """Application-facing service for loading scheduling data from TimeOffice."""

    def __init__(
        self,
        *,
        facts: TimeOfficeFacts,
        database: TimeOfficeDatabase,
    ) -> None:
        self._facts = facts
        self._database = database

    def fetch_dataset(
        self,
        *,
        planning_unit_ids: tuple[int, ...],
        planning_month: PlanningMonth,
    ) -> ValidatedSchedulingDataset:
        selected_planning_unit_ids = self._normalize_planning_unit_ids(planning_unit_ids)

        logger.info(
            "Fetching TimeOffice dataset: planning_units=%s planning_month=%s",
            planning_unit_ids,
            planning_month.label,
        )
        dataset = self._database.fetch_dataset(
            selected_planning_unit_ids=selected_planning_unit_ids,
            planning_month=planning_month,
        )
        logger.info(
            "Fetched TimeOffice dataset: planning_units=%s plans=%s employees=%s "
            "memberships=%s shifts=%s assignments=%s availability=%s "
            "minimum_staffing_requirements=%s wishes=%s",
            len(dataset.planning_units),
            len(dataset.plans),
            len(dataset.employees),
            len(dataset.planning_unit_memberships),
            len(dataset.shifts),
            len(dataset.assignments),
            len(dataset.availability),
            len(dataset.demand_requirements),
            len(dataset.wishes),
        )
        return dataset

    def _normalize_planning_unit_ids(
        self,
        planning_unit_ids: tuple[int, ...],
    ) -> tuple[int, ...]:
        normalized = tuple(dict.fromkeys(int(value) for value in planning_unit_ids))

        if not normalized:
            raise ValueError("At least one planning unit must be selected.")

        unknown_ids = sorted(
            planning_unit_id
            for planning_unit_id in normalized
            if planning_unit_id not in self._facts.planning_unit_kind_map
        )
        if unknown_ids:
            raise ValueError(
                "Unknown TimeOffice planning_unit_ids requested: "
                f"{unknown_ids}. Add them to TIMEOFFICE_FACTS.planning_unit_kind_map "
                "or fix the request."
            )

        return normalized

    def write_solution_dry_run(self, solution: Solution) -> None:
        """Log generated assignments that would later be written to TimeOffice."""
        if solution.status not in {SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE}:
            logger.info(
                "Skipping TimeOffice writeback dry-run because solution is not feasible: status=%s",
                solution.status.value,
            )
            return

        generated_assignments = [
            assignment for assignment in solution.assignments if assignment.assignment_type == AssignmentType.GENERATED
        ]

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
