from collections.abc import Generator
from contextlib import contextmanager
from datetime import date, timedelta
from threading import Lock

from sqlalchemy import Connection, Engine

from app.domain import (
    POLICY,
    Assignment,
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
    PublicationProblem,
    PublicationRejected,
    PublicationResult,
    ScheduleContext,
    SchedulingDataset,
    Shift,
    Wish,
    WishEntry,
    build_inspection,
    build_scheduling_dataset,
    expand_pattern,
    inspection_employee_ids,
    month_calendar,
)
from app.timeoffice import project_tables, queries, roster
from app.timeoffice.database import TimeOfficeConflict, TimeOfficeUnavailable
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
        self._publication_lock = Lock()
        self._serializable = engine.execution_options(isolation_level="SERIALIZABLE")

    def get_planning_options(self, *, planning_month: PlanningMonth) -> PlanningOptions:
        """Named stations that have a full-month target plan in TimeOffice."""
        with self._engine.connect() as connection:
            units = queries.read_units(connection, self._facts)
            stations = [unit.planning_unit_id for unit in units if unit.type == PlanningUnitType.STATION]
            planned = queries.read_target_plans(connection, self._facts, stations, planning_month)
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

        Worked roster rows enter generation only from trusted context plans around the month; other
        plans, including earlier output in the target plan, contribute approved absences only.
        """
        selected = tuple(dict.fromkeys(planning_unit_ids))
        with self._engine.connect() as connection:
            inspection = self._inspect(connection, selected, planning_month)
            shifts = queries.read_shifts(connection, self._facts)
            demands = tuple(project_tables.read_demand(connection, unit_id, planning_month) for unit_id in selected)
            employee_ids = [row.employee_id for row in inspection.employees]
            context = self._read_context(connection, planning_month, employee_ids, shifts)
        return build_scheduling_dataset(inspection=inspection, shifts=shifts, demands=demands, context=context)

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
                absences=queries.read_absences(
                    connection, self._facts, [employee_id], planning_month.start, planning_month.end
                ),
                availability=project_tables.read_availability(
                    connection, [employee_id], planning_month.start, planning_month.end
                ),
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

    def publish(
        self, *, planning_month: PlanningMonth, planning_unit_ids: tuple[int, ...], assignments: tuple[Assignment, ...]
    ) -> PublicationResult:
        """Replace the published duties of the named stations' month with `assignments`, or change nothing.

        Everything is validated before the old duties are deleted, inside the writing transaction: the stations
        and their single target plans, duties of those stations in the month with reference shifts and one per
        employee and date, a membership profession booking each duty's qualification, and no absence or other
        duty of the employee that date (`PublicationRejected`, conflict). The written duties are read back before
        the commit (`PublicationRejected`, read_back). An empty schedule is refused; `clear` removes published duties.
        """
        if not assignments:
            raise InvalidSelection("An empty schedule is not published; clear the stations instead.")
        with self._replacing(planning_unit_ids, planning_month) as (connection, plans, removed):
            plan_ids = list(plans.values())
            shifts = queries.read_shifts(connection, self._facts)
            rows = roster.duty_rows(connection, self._facts, plans, shifts, planning_month, assignments)
            roster.delete_output(connection, self._facts, plan_ids)
            roster.insert_rows(connection, rows)
            written = roster.read_output(connection, self._facts, plan_ids, shifts)
            if len(written) != len(assignments) or set(written) != set(assignments):
                raise PublicationRejected(
                    PublicationProblem.READ_BACK, "The published duties read back differently; nothing was changed."
                )
        return PublicationResult(
            planning_month=planning_month,
            planning_unit_ids=tuple(plans),
            removed_duties=removed,
            published_duties=len(written),
        )

    def clear(self, *, planning_month: PlanningMonth, planning_unit_ids: tuple[int, ...]) -> PublicationResult:
        """Remove the published duties of exactly the named stations' month; absences, wishes and other plans stay."""
        with self._replacing(planning_unit_ids, planning_month) as (connection, plans, removed):
            roster.delete_output(connection, self._facts, list(plans.values()))
        return PublicationResult(
            planning_month=planning_month, planning_unit_ids=tuple(plans), removed_duties=removed, published_duties=0
        )

    @contextmanager
    def _replacing(
        self, planning_unit_ids: tuple[int, ...], month: PlanningMonth
    ) -> Generator[tuple[Connection, dict[int, int], int]]:
        """One publication transaction: the stations' target plans by station and their published duty count.

        Publication and clear run one at a time in this process, each serializable, so a concurrent writer
        elsewhere makes one of them fail and roll back instead of interleaving. Any failure before the commit
        rolls back; a failure of the commit itself leaves the outcome unknown (`TimeOfficeUnavailable`, commit).
        """
        with self._publication_lock, self._serializable.connect() as connection:
            transaction = connection.begin()
            try:
                plans = self._require_stations(connection, tuple(dict.fromkeys(planning_unit_ids)), month)
                yield connection, plans, roster.count_output(connection, self._facts, list(plans.values()))
            except BaseException:
                transaction.rollback()
                raise
            try:
                transaction.commit()
            except TimeOfficeUnavailable, TimeOfficeConflict:
                raise TimeOfficeUnavailable(
                    "commit", "TimeOffice failed while committing; whether the change was saved is unknown."
                ) from None

    def _inspect(
        self, connection: Connection, selected: tuple[int, ...], planning_month: PlanningMonth
    ) -> PlanningInspection:
        units, memberships, employee_ids = self._selection_scope(connection, selected, planning_month)
        employees = queries.read_employees(connection, self._facts, employee_ids)
        start, end = planning_month.start, planning_month.end
        absences = queries.read_absences(connection, self._facts, employee_ids, start, end)
        accounts = queries.read_accounts(connection, self._facts, employee_ids, planning_month, absences)
        availability = project_tables.read_availability(connection, employee_ids, start, end)

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
            shifts=queries.read_shift_options(connection, self._facts),
        )

    def _read_context(
        self, connection: Connection, month: PlanningMonth, employee_ids: list[int], shifts: tuple[Shift, ...]
    ) -> ScheduleContext:
        """Trusted duties of the dates the month's rules reach that context plans span without a gap.

        A context duty inside the month would be fixed input, which generation does not support, so it fails.
        """
        day = timedelta(days=1)
        spanned = queries.read_context_coverage(
            connection,
            self._facts,
            month.start - POLICY.preceding_context_days * day,
            month.end + POLICY.following_context_days * day,
        )
        covered_from, covered_until = month.start, month.end
        while covered_from - day in spanned:
            covered_from -= day
        while covered_until + day in spanned:
            covered_until += day
        duties = queries.read_context_duties(connection, self._facts, employee_ids, covered_from, covered_until, shifts)
        if any(row.date in month for row in duties):
            raise ValueError("Trusted context plans contain duties inside the planning month.")
        after = month.end + day
        return ScheduleContext(
            covered_from=covered_from,
            covered_until=covered_until,
            duties=duties,
            availability=(
                *queries.read_absences(connection, self._facts, employee_ids, after, after),
                *project_tables.read_availability(connection, employee_ids, after, after),
            ),
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

    def _require_stations(
        self, connection: Connection, selected: tuple[int, ...], month: PlanningMonth
    ) -> dict[int, int]:
        """The target plan ID of each selected configured station, by station; anything else fails."""
        unit_types = self._facts.planning_unit_type_by_id
        if not selected:
            raise InvalidSelection("At least one station must be selected.")
        if any(unit_types.get(unit_id) != PlanningUnitType.STATION for unit_id in selected):
            raise InvalidSelection("Select configured stations; a jumper pool is origin context only.")
        plans = queries.read_target_plans(connection, self._facts, selected, month)
        if missing := set(selected) - plans.keys():
            raise InvalidSelection(f"No TimeOffice target plan for planning_unit_ids={sorted(missing)}.")
        return plans

    def _require_employee(self, connection: Connection, employee_id: int, month: PlanningMonth) -> None:
        """Availability and wishes belong to employees with a membership in a configured unit that month."""
        if employee_id not in queries.read_planned_employee_ids(connection, self._facts, [employee_id], month):
            raise InvalidSelection(f"Employee {employee_id} has no planning membership in the month.")

    def _require_shifts(self, shift_ids: tuple[int, ...]) -> None:
        if unknown := set(shift_ids) - self._facts.reference_shift_ids:
            raise InvalidSelection(f"Unknown shift_ids={sorted(unknown)}; use the reference shifts.")


def _month_of(day: date) -> PlanningMonth:
    return PlanningMonth(year=day.year, month=day.month)
