from datetime import timedelta

from sqlalchemy import Connection

from scheduling.domain import (
    DemandRequirement,
    PlanningPeriod,
    PlanningUnit,
    PlanningUnitKind,
    SchedulingBaseModel,
    Shift,
    StaffingDemandRole,
)
from scheduling.domain.employee import StaffLevel
from scheduling.timeoffice.facts import TimeOfficeDemandFact, TimeOfficeFacts


class DemandRepositoryResult(SchedulingBaseModel):
    demand_requirements: tuple[DemandRequirement, ...]


class TimeOfficeDemandRepository:
    """Reads TimeOffice demand/Bedarf.

    The test database currently has no usable `TBenutzerBedarf*` rows for the
    selected planning units. Therefore this repository is facts-backed for now.

    Later, the internals can be replaced or extended with DB-backed reads from:
    - TBenutzerBedarfsGruppen
    - TBenutzerBedarf
    - TBenutzerBedarfTagTypGruppe

    The output contract stays `DemandRequirement`.
    """

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(
        self,
        *,
        connection: Connection,
        period: PlanningPeriod,
        planning_units: tuple[PlanningUnit, ...],
        shifts: tuple[Shift, ...],
    ) -> DemandRepositoryResult:
        # Kept in the signature because demand is architecturally source-backed.
        # The current fallback implementation does not need DB rows yet.
        _ = connection

        return DemandRepositoryResult(
            demand_requirements=self._build_from_facts(
                period=period,
                planning_units=planning_units,
                shifts=shifts,
            )
        )

    def _build_from_facts(
        self,
        *,
        period: PlanningPeriod,
        planning_units: tuple[PlanningUnit, ...],
        shifts: tuple[Shift, ...],
    ) -> tuple[DemandRequirement, ...]:
        shifts_by_id = {shift.shift_id: shift for shift in shifts}

        station_planning_units = tuple(
            planning_unit for planning_unit in planning_units if planning_unit.kind == PlanningUnitKind.STATION
        )

        requirements_by_key: dict[
            tuple[int, object, int, StaffLevel],
            DemandRequirement,
        ] = {}

        current_date = period.start
        while current_date <= period.end:
            iso_weekday = current_date.isoweekday()

            for planning_unit in station_planning_units:
                for fact in self._facts.demand_facts:
                    if not self._applies_to_planning_unit(
                        fact=fact,
                        planning_unit_id=planning_unit.planning_unit_id,
                    ):
                        continue

                    shift = shifts_by_id.get(fact.source_shift_id)
                    if shift is None:
                        raise ValueError(f"TimeOffice demand fact references unknown shift_id={fact.source_shift_id}.")

                    if shift.staffing_role != StaffingDemandRole.REQUIRED_MINIMUM:
                        raise ValueError(
                            "TimeOffice demand fact must reference a REQUIRED_MINIMUM shift: "
                            f"shift_id={shift.shift_id} staffing_role={shift.staffing_role}."
                        )

                    required_count = fact.required_by_iso_weekday.get(iso_weekday)
                    if required_count is None:
                        raise ValueError(
                            "TimeOffice demand fact missing ISO weekday "
                            f"{iso_weekday}: shift_id={fact.source_shift_id} "
                            f"staff_level={fact.staff_level}."
                        )

                    if required_count <= 0:
                        continue

                    requirement = DemandRequirement(
                        planning_unit_id=planning_unit.planning_unit_id,
                        date=current_date,
                        shift_id=fact.source_shift_id,
                        staff_level=fact.staff_level,
                        required_count=required_count,
                    )

                    key = (
                        requirement.planning_unit_id,
                        requirement.date,
                        requirement.shift_id,
                        requirement.staff_level,
                    )

                    existing = requirements_by_key.get(key)
                    if existing is not None:
                        raise ValueError(
                            "Duplicate TimeOffice demand fact expansion: "
                            f"planning_unit_id={requirement.planning_unit_id} "
                            f"date={requirement.date} "
                            f"shift_id={requirement.shift_id} "
                            f"staff_level={requirement.staff_level}."
                        )

                    requirements_by_key[key] = requirement

            current_date += timedelta(days=1)

        return tuple(
            requirements_by_key[key]
            for key in sorted(
                requirements_by_key,
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
                    str(item[3]),
                ),
            )
        )

    def _applies_to_planning_unit(
        self,
        *,
        fact: TimeOfficeDemandFact,
        planning_unit_id: int,
    ) -> bool:
        return fact.planning_unit_ids is None or planning_unit_id in fact.planning_unit_ids
