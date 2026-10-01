import logging

from sqlalchemy import Engine

from app.domain import (
    PlanningMonth,
    PlanningUnitType,
    SchedulingDataset,
)
from app.employees.inspection import build_inspection, inspection_employee_ids
from app.employees.models import PlanningInspection, PlanningOptions
from app.solver.models import Solution
from app.timeoffice.facts import TimeOfficeFacts
from app.timeoffice.mapping import map_scheduling_dataset
from app.timeoffice.mapping.options import map_planning_units
from app.timeoffice.mapping.personnel import map_employees, map_planning_unit_memberships
from app.timeoffice.mapping.roster import map_availability
from app.timeoffice.mapping.work_accounts import map_monthly_work_accounts
from app.timeoffice.reading.container import TimeOfficeReaders
from app.timeoffice.reading.employee_evidence import read_employee_evidence
from app.timeoffice.writing.solution import LegacySolutionExportPaths, TimeOfficeSolutionWriter
from app.validation import validate_scheduling_dataset

logger = logging.getLogger(__name__)


class TimeOfficeService:
    """Application-facing service for TimeOffice reads and solver compatibility exports."""

    def __init__(
        self,
        *,
        facts: TimeOfficeFacts,
        engine: Engine,
        readers: TimeOfficeReaders,
        solution_writer: TimeOfficeSolutionWriter,
    ) -> None:
        self._facts = facts
        self._engine = engine
        self._readers = readers
        self._solution_writer = solution_writer

    def get_planning_options(self, *, planning_month: PlanningMonth) -> PlanningOptions:
        """Return named station destinations with unique full-month targets, without provisioning.

        Raises:
            ValueError: Configured names or target selection are ambiguous/incomplete.
        """
        with self._engine.connect() as connection:
            units = map_planning_units(
                rows=self._readers.options.read_planning_unit_option_rows(connection=connection), facts=self._facts
            )
            station_ids = tuple(unit.planning_unit_id for unit in units if unit.type == PlanningUnitType.STATION)
            rows = self._readers.planning_units.read_rows(
                connection=connection,
                selected_planning_unit_ids=station_ids,
                planning_month=planning_month,
                require_all=False,
            )
        available_ids = {row.planning_unit_id for row in rows}
        return PlanningOptions(
            planning_month=planning_month,
            planning_units=tuple(unit for unit in units if unit.planning_unit_id in available_ids),
        )

    def inspect_employees(
        self, *, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth
    ) -> PlanningInspection:
        """Read the entire station/pool scope or fail before returning any employees.

        No demand, prior output, plan-personnel artifacts or write/provisioning paths
        are used. Every employee needs complete account and monthly evidence.

        Raises:
            ValueError: Selection or employee source facts are incomplete/ambiguous.
        """
        selected = self._normalize_planning_unit_ids(planning_unit_ids)
        if any(self._facts.planning_unit_type_by_id[unit_id] != PlanningUnitType.STATION for unit_id in selected):
            raise ValueError("Select station destinations; a shared pool is origin context only.")
        with self._engine.connect() as connection:
            # Validate all selected target plans without loading prior generated output.
            self._readers.planning_units.read_rows(
                connection=connection,
                selected_planning_unit_ids=selected,
                planning_month=planning_month,
            )
            units = map_planning_units(
                rows=self._readers.options.read_planning_unit_option_rows(connection=connection), facts=self._facts
            )
            all_rows = self._readers.personnel.read_membership_rows(
                connection=connection,
                planning_unit_ids=tuple(unit.planning_unit_id for unit in units),
                planning_month=planning_month,
            )
            relevant_employee_ids = inspection_employee_ids(
                selected_station_ids=selected,
                memberships=all_rows,
                shared_pool_ids={unit.planning_unit_id for unit in units if unit.type == PlanningUnitType.SHARED_POOL},
            )
            memberships = tuple(row for row in all_rows if row.employee_id in relevant_employee_ids)
            employee_ids = tuple(sorted(relevant_employee_ids))
            employees = map_employees(
                self._readers.personnel.read_employee_rows(
                    connection=connection,
                    employee_ids=employee_ids,
                ),
                facts=self._facts,
            )
            accounts = map_monthly_work_accounts(
                self._readers.monthly_work_accounts.read_rows(
                    connection=connection,
                    employee_ids=employee_ids,
                    planning_month=planning_month,
                )
            )
            evidence = read_employee_evidence(
                connection=connection,
                employee_ids=employee_ids,
                planning_month=planning_month,
            )
            availability = map_availability(
                rows=self._readers.roster.read_rows(
                    connection=connection,
                    employee_ids=employee_ids,
                    planning_month=planning_month,
                ),
                facts=self._facts,
            )
        canonical_memberships = map_planning_unit_memberships(memberships, facts=self._facts)
        relevant_unit_ids = set(selected) | {row.planning_unit_id for row in canonical_memberships}
        if not set(selected) <= {unit.planning_unit_id for unit in units}:
            raise ValueError("Selected station names are missing.")
        return build_inspection(
            planning_month=planning_month,
            selected_station_ids=selected,
            units=tuple(unit for unit in units if unit.planning_unit_id in relevant_unit_ids),
            employees=employees,
            memberships=canonical_memberships,
            accounts=accounts,
            evidence=evidence,
            availability=availability,
            allowed_shift_ids=set(self._facts.reference_shift_facts_by_id),
        )

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
