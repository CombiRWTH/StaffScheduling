from sqlalchemy import Engine

from app.domain import (
    InvalidSelection,
    PlanningInspection,
    PlanningMonth,
    PlanningOptions,
    PlanningUnitType,
    build_inspection,
    inspection_employee_ids,
)
from app.timeoffice import queries
from app.timeoffice.facts import TIMEOFFICE_FACTS, TimeOfficeFacts


class TimeOfficeService:
    """The TimeOffice adapter's whole interface: canonical models in and out; SQL and source terms stay inside.

    Methods raise `InvalidSelection` for stations that cannot be planned in the month, `ValueError`
    for incomplete or ambiguous source data and `TimeOfficeUnavailable` when the database cannot be reached.
    """

    def __init__(self, engine: Engine, facts: TimeOfficeFacts = TIMEOFFICE_FACTS) -> None:
        self._engine = engine
        self._facts = facts

    def get_planning_options(self, *, planning_month: PlanningMonth) -> PlanningOptions:
        """Named stations that have a full-month target plan in TimeOffice."""
        with self._engine.connect() as connection:
            units = queries.read_units(connection, self._facts)
            stations = [unit.planning_unit_id for unit in units if unit.type == PlanningUnitType.STATION]
            planned = queries.read_units_with_target_plan(connection, self._facts, stations, planning_month)
        return PlanningOptions(
            planning_month=planning_month,
            planning_units=tuple(unit for unit in units if unit.planning_unit_id in planned),
        )

    def inspect_employees(
        self, *, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth
    ) -> PlanningInspection:
        """The complete read-only employee scope of the selected stations and their pool, or an error."""
        selected = tuple(dict.fromkeys(planning_unit_ids))
        unit_types = self._facts.planning_unit_type_by_id
        if not selected:
            raise InvalidSelection("At least one station must be selected.")
        if any(unit_types.get(unit_id) != PlanningUnitType.STATION for unit_id in selected):
            raise InvalidSelection("Select configured stations; a shared pool is origin context only.")

        with self._engine.connect() as connection:
            if missing := set(selected) - queries.read_units_with_target_plan(
                connection, self._facts, selected, planning_month
            ):
                raise InvalidSelection(f"No TimeOffice target plan for planning_unit_ids={sorted(missing)}.")
            units = queries.read_units(connection, self._facts)
            memberships = queries.read_memberships(
                connection, self._facts, [unit.planning_unit_id for unit in units], planning_month
            )
            employee_ids = sorted(
                inspection_employee_ids(
                    selected_station_ids=selected,
                    memberships=memberships,
                    shared_pool_ids={u.planning_unit_id for u in units if u.type == PlanningUnitType.SHARED_POOL},
                )
            )
            employees = queries.read_employees(connection, self._facts, employee_ids)
            accounts = queries.read_accounts(connection, self._facts, employee_ids, planning_month)
            absences = queries.read_absences(connection, self._facts, employee_ids, planning_month)
            evidence = queries.read_evidence(connection, employee_ids, planning_month)

        scope_memberships = tuple(row for row in memberships if row.employee_id in employee_ids)
        relevant_unit_ids = set(selected) | {row.planning_unit_id for row in scope_memberships}
        return build_inspection(
            planning_month=planning_month,
            selected_station_ids=selected,
            units=tuple(unit for unit in units if unit.planning_unit_id in relevant_unit_ids),
            employees=employees,
            memberships=scope_memberships,
            accounts=accounts,
            evidence=evidence,
            availability=absences,
            allowed_shift_ids=set(self._facts.reference_shift_ids),
        )
