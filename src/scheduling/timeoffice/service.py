import logging

from sqlalchemy import Engine

from scheduling.api.solve.schemas import SolveOptions
from scheduling.domain import PlanningMonth, SchedulingDataset, Wish
from scheduling.solver.models import Solution
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.mapping import map_scheduling_dataset
from scheduling.timeoffice.mapping.options import map_solve_options
from scheduling.timeoffice.reading.container import TimeOfficeReaders
from scheduling.timeoffice.writing.solution import LegacySolutionExportPaths, TimeOfficeSolutionWriter
from scheduling.timeoffice.writing.wishes import TimeOfficeWishWriter
from scheduling.validation import validate_scheduling_dataset

logger = logging.getLogger(__name__)


class TimeOfficeService:
    """Application-facing service for TimeOffice reads and allowed writebacks."""

    def __init__(
        self,
        *,
        facts: TimeOfficeFacts,
        engine: Engine,
        readers: TimeOfficeReaders,
        solution_writer: TimeOfficeSolutionWriter,
        wish_writer: TimeOfficeWishWriter,
    ) -> None:
        self._facts = facts
        self._engine = engine
        self._readers = readers
        self._solution_writer = solution_writer
        self._wish_writer = wish_writer

    def get_solve_options(self) -> SolveOptions:
        logger.info("Fetching TimeOffice solve options")

        with self._engine.connect() as connection:
            rows = self._readers.options.read_planning_unit_option_rows(connection=connection)

        options = map_solve_options(rows=rows, facts=self._facts)

        logger.info(
            "Fetched TimeOffice solve options: planning_units=%s",
            len(options.planning_units),
        )

        return options

    def fetch_dataset(
        self,
        *,
        planning_unit_ids: tuple[int, ...],
        planning_month: PlanningMonth,
    ) -> SchedulingDataset:
        selected_planning_unit_ids = self._normalize_planning_unit_ids(planning_unit_ids)

        logger.info(
            "Fetching TimeOffice sources: planning_units=%s planning_month=%s",
            selected_planning_unit_ids,
            planning_month.label,
        )

        with self._engine.connect() as connection:
            sources = self._readers.read_sources(
                connection=connection,
                selected_planning_unit_ids=selected_planning_unit_ids,
                planning_month=planning_month,
            )

        dataset = map_scheduling_dataset(
            sources=sources,
            facts=self._facts,
            planning_month=planning_month,
        )

        validated_dataset = validate_scheduling_dataset(dataset)

        logger.info(
            "Fetched TimeOffice dataset: planning_units=%s plans=%s employees=%s "
            "memberships=%s shifts=%s assignments=%s availability=%s "
            "minimum_staffing_requirements=%s wishes=%s monthly_work_accounts=%s "
            "source_plan_personnel_rows=%s",
            len(validated_dataset.planning_units),
            len(validated_dataset.plans),
            len(validated_dataset.employees),
            len(validated_dataset.planning_unit_memberships),
            len(validated_dataset.shifts),
            len(validated_dataset.assignments),
            len(validated_dataset.availability),
            len(validated_dataset.demand_requirements),
            len(validated_dataset.wishes),
            len(validated_dataset.monthly_work_accounts),
            len(sources.plan_personnel_rows),
        )

        return validated_dataset

    def write_solution_dry_run(self, solution: Solution) -> None:
        self._solution_writer.write_dry_run(solution)

    def write_solution_legacy_format(
        self,
        *,
        dataset: SchedulingDataset,
        solution: Solution,
        solution_name: str,
    ) -> LegacySolutionExportPaths | None:
        return self._solution_writer.write_legacy_format(
            dataset=dataset,
            solution=solution,
            solution_name=solution_name,
        )

    def _normalize_planning_unit_ids(
        self,
        planning_unit_ids: tuple[int, ...],
    ) -> tuple[int, ...]:
        normalized = tuple(dict.fromkeys(planning_unit_ids))

        if not normalized:
            raise ValueError("At least one planning unit must be selected.")

        unknown_ids = sorted(
            planning_unit_id
            for planning_unit_id in normalized
            if planning_unit_id not in self._facts.planning_unit_type_by_id
        )
        if unknown_ids:
            known_ids = sorted(self._facts.planning_unit_type_by_id)
            raise ValueError(
                f"Unknown TimeOffice planning_unit_ids requested: {unknown_ids}. Known planning_unit_ids={known_ids}."
            )

        return normalized

    def replace_wishes(
        self,
        *,
        planning_unit_id: int,
        planning_month: PlanningMonth,
        employee_id: int,
        wishes: tuple[Wish, ...],
    ) -> None:
        with self._engine.begin() as connection:
            self._wish_writer.delete_employee_wishes(
                connection=connection,
                planning_unit_id=planning_unit_id,
                planning_month=planning_month,
                employee_id=employee_id,
            )

            self._wish_writer.insert_wishes(
                connection=connection,
                planning_unit_id=planning_unit_id,
                planning_month=planning_month,
                wishes=wishes,
                facts=self._facts,
            )

    def delete_employee_wishes(
        self,
        *,
        planning_unit_id: int,
        planning_month: PlanningMonth,
        employee_id: int,
    ) -> None:
        with self._engine.begin() as connection:
            self._wish_writer.delete_employee_wishes(
                connection=connection,
                planning_unit_id=planning_unit_id,
                planning_month=planning_month,
                employee_id=employee_id,
            )
