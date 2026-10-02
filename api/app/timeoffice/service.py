from datetime import date

from sqlalchemy import Connection, Engine

from app.domain import (
    Availability,
    AvailabilityEntry,
    DemandConfiguration,
    DemandPattern,
    EmployeeCalendar,
    EmployeeSummary,
    InvalidSelection,
    MonthlyDemand,
    PlanningInspection,
    PlanningMonth,
    PlanningOptions,
    PlanningUnit,
    PlanningUnitMembership,
    PlanningUnitType,
    SchedulingDataset,
    Wish,
    WishEntry,
    build_inspection,
    build_scheduling_dataset,
    expand_pattern,
    inspection_employee_ids,
    month_calendar,
)
from app.timeoffice import project_tables, queries
from app.timeoffice.facts import TIMEOFFICE_FACTS, TimeOfficeFacts


class TimeOfficeService:
    """The TimeOffice adapter's whole interface: canonical models in and out; SQL and source terms stay inside.

    Methods raise `InvalidSelection` for requests that cannot be planned in the month, `ValueError`
    for incomplete or ambiguous source data and `TimeOfficeUnavailable` when the database cannot be reached.
    Writes validate before mutating and commit in one transaction.
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
        """The complete read-only employee scope of the selected stations and their jumper pools, or an error."""
        with self._engine.connect() as connection:
            return self._inspect(connection, tuple(dict.fromkeys(planning_unit_ids)), planning_month)

    def read_generation_input(
        self, *, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth
    ) -> SchedulingDataset:
        """The full-month solver input of the selected stations, or an error.

        Roster rows are read only as approved absences; worked shifts of any plan, including earlier
        output in the target plan, never enter generation.
        """
        selected = tuple(dict.fromkeys(planning_unit_ids))
        with self._engine.connect() as connection:
            inspection = self._inspect(connection, selected, planning_month)
            shifts = queries.read_shifts(connection, self._facts)
            demands = tuple(project_tables.read_demand(connection, unit_id, planning_month) for unit_id in selected)
        return build_scheduling_dataset(inspection=inspection, shifts=shifts, demands=demands)

    def list_employees(
        self, *, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth
    ) -> tuple[EmployeeSummary, ...]:
        """The selection's employees by name, without requiring their monthly accounts."""
        selected = tuple(dict.fromkeys(planning_unit_ids))
        with self._engine.connect() as connection:
            _, _, employee_ids = self._selection_scope(connection, selected, planning_month)
            employees = queries.read_employees(connection, self._facts, employee_ids)
        return tuple(EmployeeSummary(employee_id=row.employee_id, display_name=row.display_name) for row in employees)

    def get_employee_calendar(self, *, employee_id: int, planning_month: PlanningMonth) -> EmployeeCalendar:
        """One employee's native absences, project availability and wishes in the month."""
        with self._engine.connect() as connection:
            self._require_employee(connection, employee_id, planning_month)
            return EmployeeCalendar(
                employee_id=employee_id,
                planning_month=planning_month,
                absences=queries.read_absences(connection, self._facts, [employee_id], planning_month),
                availability=project_tables.read_availability(connection, [employee_id], planning_month),
                wishes=project_tables.read_wishes(connection, [employee_id], planning_month),
                calendar=month_calendar(planning_month),
                shifts=queries.read_shift_options(connection, self._facts),
            )

    def set_availability(self, *, employee_id: int, day: date, entry: AvailabilityEntry | None) -> None:
        """Replace the project availability of exactly this employee and date; `None` removes it."""
        self._require_shifts(entry.shift_ids or () if entry else ())
        with self._engine.begin() as connection:
            self._require_employee(connection, employee_id, _month_of(day))
            project_tables.delete_availability(connection, employee_id, day)
            if entry:
                project_tables.insert_availability(
                    connection, Availability(employee_id=employee_id, date=day, **entry.model_dump())
                )

    def set_wish(self, *, employee_id: int, day: date, entry: WishEntry | None) -> None:
        """Replace the wish of exactly this employee and date; `None` removes it."""
        self._require_shifts((entry.shift_id,) if entry and entry.shift_id else ())
        with self._engine.begin() as connection:
            self._require_employee(connection, employee_id, _month_of(day))
            project_tables.delete_wish(connection, employee_id, day)
            if entry:
                project_tables.insert_wish(connection, Wish(employee_id=employee_id, date=day, **entry.model_dump()))

    def get_demand(self, *, planning_unit_id: int, planning_month: PlanningMonth) -> DemandConfiguration:
        """The saved dated demand of one station month (None if never saved), with its calendar and shifts."""
        with self._engine.connect() as connection:
            self._require_stations(connection, (planning_unit_id,), planning_month)
            return DemandConfiguration(
                planning_unit_id=planning_unit_id,
                planning_month=planning_month,
                demand=project_tables.read_demand(connection, planning_unit_id, planning_month),
                calendar=month_calendar(planning_month),
                shifts=queries.read_shift_options(connection, self._facts),
            )

    def save_demand(self, demand: MonthlyDemand) -> None:
        """Replace the complete demand of one station month; an empty month saves 'nobody required'."""
        self._require_shifts(tuple(cell.shift_id for cell in demand.cells))
        with self._engine.begin() as connection:
            self._require_stations(connection, (demand.planning_unit_id,), demand.planning_month)
            project_tables.replace_demand(connection, demand)

    def preview_demand(self, pattern: DemandPattern) -> MonthlyDemand:
        """The month a weekly pattern would produce for a plannable station; nothing is saved."""
        self._require_shifts(tuple(cell.shift_id for cell in pattern.cells))
        with self._engine.connect() as connection:
            self._require_stations(connection, (pattern.planning_unit_id,), pattern.planning_month)
        return expand_pattern(pattern)

    def _inspect(
        self, connection: Connection, selected: tuple[int, ...], planning_month: PlanningMonth
    ) -> PlanningInspection:
        units, memberships, employee_ids = self._selection_scope(connection, selected, planning_month)
        employees = queries.read_employees(connection, self._facts, employee_ids)
        accounts = queries.read_accounts(connection, self._facts, employee_ids, planning_month)
        absences = queries.read_absences(connection, self._facts, employee_ids, planning_month)
        availability = project_tables.read_availability(connection, employee_ids, planning_month)

        scope_memberships = tuple(row for row in memberships if row.employee_id in employee_ids)
        relevant_unit_ids = set(selected) | {row.planning_unit_id for row in scope_memberships}
        return build_inspection(
            planning_month=planning_month,
            selected_station_ids=selected,
            units=tuple(unit for unit in units if unit.planning_unit_id in relevant_unit_ids),
            employees=employees,
            memberships=scope_memberships,
            accounts=accounts,
            availability=(*absences, *availability),
            allowed_shift_ids=set(self._facts.reference_shift_ids),
        )

    def _selection_scope(
        self, connection: Connection, selected: tuple[int, ...], month: PlanningMonth
    ) -> tuple[tuple[PlanningUnit, ...], tuple[PlanningUnitMembership, ...], list[int]]:
        """Configured units, month memberships and the selection's employee IDs (stations plus home jumper pools)."""
        self._require_stations(connection, selected, month)
        units = queries.read_units(connection, self._facts)
        memberships = queries.read_memberships(
            connection, self._facts, [unit.planning_unit_id for unit in units], month
        )
        employee_ids = inspection_employee_ids(
            selected_station_ids=selected,
            memberships=memberships,
            jumper_pool_ids={unit.planning_unit_id for unit in units if unit.type == PlanningUnitType.JUMPER_POOL},
        )
        return units, memberships, sorted(employee_ids)

    def _require_stations(self, connection: Connection, selected: tuple[int, ...], month: PlanningMonth) -> None:
        unit_types = self._facts.planning_unit_type_by_id
        if not selected:
            raise InvalidSelection("At least one station must be selected.")
        if any(unit_types.get(unit_id) != PlanningUnitType.STATION for unit_id in selected):
            raise InvalidSelection("Select configured stations; a jumper pool is origin context only.")
        if missing := set(selected) - queries.read_units_with_target_plan(connection, self._facts, selected, month):
            raise InvalidSelection(f"No TimeOffice target plan for planning_unit_ids={sorted(missing)}.")

    def _require_employee(self, connection: Connection, employee_id: int, month: PlanningMonth) -> None:
        """Availability and wishes belong to employees with a membership in a configured unit that month."""
        if employee_id not in queries.read_planned_employee_ids(connection, self._facts, [employee_id], month):
            raise InvalidSelection(f"Employee {employee_id} has no planning membership in the month.")

    def _require_shifts(self, shift_ids: tuple[int, ...]) -> None:
        if unknown := set(shift_ids) - self._facts.reference_shift_ids:
            raise InvalidSelection(f"Unknown shift_ids={sorted(unknown)}; use the reference shifts.")


def _month_of(day: date) -> PlanningMonth:
    return PlanningMonth(year=day.year, month=day.month)
