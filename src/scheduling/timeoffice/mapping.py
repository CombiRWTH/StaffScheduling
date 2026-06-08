from src.scheduling.models import SchedulingDataset, Station, StationMonthData
from src.scheduling.models.employee import Employee
from src.scheduling.models.relations import Membership
from src.scheduling.timeoffice.models import TimeOfficeSourceData
from src.scheduling.timeoffice.settings import TimeOfficeSettings
from src.scheduling.timeoffice.source_models import TimeOfficePlanEmployeeSource, TimeOfficePlanSource


class TimeOfficeMapper:
    """Map TimeOffice source data to canonical scheduling data.

    Boundary rules:
    - May know TimeOffice source meanings and mapping rules.
    - Must not query the database.
    - Must not read/write cache files.
    - Must not create solver variables or solver input.
    """

    def __init__(self, settings: TimeOfficeSettings):
        self._settings = settings

    def to_station_month_data(self, source_data: TimeOfficeSourceData) -> tuple[StationMonthData, ...]:
        """Map TimeOffice source data into one StationMonthData object per station."""
        print("[timeoffice] mapper.to_station_month_data")

        plans_by_station = {plan.station_id: plan for plan in source_data.plans}

        return tuple(
            self._map_station_month_data(
                station_id=station_id,
                source_data=source_data,
                plan=plans_by_station.get(station_id),
            )
            for station_id in source_data.station_ids
        )

    def _map_station_month_data(
        self,
        station_id: int,
        source_data: TimeOfficeSourceData,
        plan: TimeOfficePlanSource | None,
    ) -> StationMonthData:
        """Map one station's TimeOffice source data into StationMonthData."""
        plan_employees = tuple(
            plan_employee for plan_employee in source_data.plan_employees if plan_employee.station_id == station_id
        )

        return StationMonthData(
            station=Station(
                station_id=station_id,
                name=None if plan is None else plan.station_name,
                source_planning_unit_id=station_id if plan is None else plan.source_planning_unit_id,
            ),
            period=source_data.period,
            source_plan_id=None if plan is None else plan.source_plan_id,
            employees=self._map_employees(plan_employees),
            memberships=self._map_memberships(plan_employees),
        )

    def _map_employees(
        self,
        plan_employees: tuple[TimeOfficePlanEmployeeSource, ...],
    ) -> tuple[Employee, ...]:
        """Map TimeOffice plan employees to canonical Employee records."""
        employees_by_id: dict[int, Employee] = {}

        for source_employee in plan_employees:
            employees_by_id[source_employee.employee_id] = Employee(
                employee_id=source_employee.employee_id,
                personnel_number=source_employee.personnel_number,
                first_name=source_employee.first_name,
                last_name=source_employee.last_name,
                display_name=self._display_name(source_employee),
                group_id=None,
                active=True,
            )

        return tuple(employees_by_id.values())

    def _map_memberships(
        self,
        plan_employees: tuple[TimeOfficePlanEmployeeSource, ...],
    ) -> tuple[Membership, ...]:
        """Map TimeOffice plan employees to local station memberships."""
        memberships_by_key: dict[tuple[int, int], Membership] = {}

        for source_employee in plan_employees:
            key = (source_employee.employee_id, source_employee.station_id)

            memberships_by_key[key] = Membership(
                employee_id=source_employee.employee_id,
                station_id=source_employee.station_id,
                membership_type="local",
                valid_from=source_employee.valid_from,
                valid_until=source_employee.valid_until,
                is_substitute=source_employee.is_substitute,
            )

        return tuple(memberships_by_key.values())

    def _display_name(self, source_employee: TimeOfficePlanEmployeeSource) -> str:
        """Build a readable employee display name."""
        name_parts = [
            source_employee.first_name,
            source_employee.last_name,
        ]
        display_name = " ".join(part for part in name_parts if part)

        if display_name:
            return display_name

        if source_employee.short_name:
            return source_employee.short_name

        if source_employee.personnel_number:
            return source_employee.personnel_number

        return f"Employee {source_employee.employee_id}"

    def combine_station_month_data(self, station_month_data: tuple[StationMonthData, ...]) -> SchedulingDataset:
        """Combine station-month data into one scheduling dataset.

        Current iteration: shallow concatenation without deduplication.
        """
        print("[timeoffice] mapper.combine_station_month_data")

        if not station_month_data:
            raise ValueError("Cannot combine empty station-month data.")

        period = station_month_data[0].period
        station_ids = tuple(data.station.station_id for data in station_month_data)

        effective_jump_pool_ids = tuple(
            station_id for station_id in station_ids if station_id in self._settings.jump_pool_station_ids
        )

        regular_station_ids = tuple(
            station_id for station_id in station_ids if station_id not in effective_jump_pool_ids
        )

        return SchedulingDataset(
            period=period,
            stations=tuple(data.station for data in station_month_data),
            regular_station_ids=regular_station_ids,
            jump_pool_station_ids=effective_jump_pool_ids,
            employees=self._unique_employees(
                tuple(employee for data in station_month_data for employee in data.employees)
            ),
            shifts=tuple(shift for data in station_month_data for shift in data.shifts),
            demand=tuple(demand for data in station_month_data for demand in data.demand),
            memberships=tuple(membership for data in station_month_data for membership in data.memberships),
            assignments=tuple(assignment for data in station_month_data for assignment in data.assignments),
            availability=tuple(item for data in station_month_data for item in data.availability),
            rules=tuple(rule for data in station_month_data for rule in data.rules),
            preferences=tuple(preference for data in station_month_data for preference in data.preferences),
        )

    def _unique_employees(self, employees: tuple[Employee, ...]) -> tuple[Employee, ...]:
        """Deduplicate employees by employee_id."""
        employees_by_id: dict[int, Employee] = {}

        for employee in employees:
            employees_by_id[employee.employee_id] = employee

        return tuple(employees_by_id.values())
