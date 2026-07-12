from dataclasses import dataclass

from sqlalchemy import Connection

from scheduling.domain import PlanningMonth
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.reading.demand import TimeOfficeDemandReader, TimeOfficeDemandRow
from scheduling.timeoffice.reading.objective_weights import TimeOfficeObjectiveWeightRow, TimeOfficeWeightsReader
from scheduling.timeoffice.reading.options import TimeOfficeOptionsReader
from scheduling.timeoffice.reading.personnel import (
    TimeOfficeEmployeeRow,
    TimeOfficePersonnelReader,
    TimeOfficePlanningUnitMembershipRow,
    TimeOfficePlanPersonnelRow,
)
from scheduling.timeoffice.reading.planning_units import TimeOfficePlanningUnitReader, TimeOfficePlanningUnitRow
from scheduling.timeoffice.reading.roster import TimeOfficeRosterReader, TimeOfficeRosterRow
from scheduling.timeoffice.reading.shifts import TimeOfficeShiftReader, TimeOfficeShiftRow
from scheduling.timeoffice.reading.sunday_work import TimeOfficeSundayHistoryRow, TimeOfficeSundayWorkHistoryReader
from scheduling.timeoffice.reading.wishes import TimeOfficeWishReader, TimeOfficeWishRow
from scheduling.timeoffice.reading.work_accounts import (
    TimeOfficeMonthlyWorkAccountReader,
    TimeOfficeMonthlyWorkAccountRow,
)


@dataclass(frozen=True, slots=True)
class TimeOfficeSources:
    """TimeOffice source rows for one selected planning month."""

    planning_unit_rows: tuple[TimeOfficePlanningUnitRow, ...]

    # TimeOffice plan artifact. Not canonical solver input.
    plan_personnel_rows: tuple[TimeOfficePlanPersonnelRow, ...]

    employee_rows: tuple[TimeOfficeEmployeeRow, ...]
    planning_unit_membership_rows: tuple[TimeOfficePlanningUnitMembershipRow, ...]

    shift_rows: tuple[TimeOfficeShiftRow, ...]
    roster_rows: tuple[TimeOfficeRosterRow, ...]
    wish_rows: tuple[TimeOfficeWishRow, ...]
    demand_rows: tuple[TimeOfficeDemandRow, ...]
    sunday_history_rows: tuple[TimeOfficeSundayHistoryRow, ...]
    monthly_work_account_rows: tuple[TimeOfficeMonthlyWorkAccountRow, ...]
    objective_weight_rows: tuple[TimeOfficeObjectiveWeightRow, ...]


@dataclass(frozen=True, slots=True)
class TimeOfficeReaders:
    options: TimeOfficeOptionsReader
    planning_units: TimeOfficePlanningUnitReader
    personnel: TimeOfficePersonnelReader
    shifts: TimeOfficeShiftReader
    roster: TimeOfficeRosterReader
    wishes: TimeOfficeWishReader
    sunday_work_history: TimeOfficeSundayWorkHistoryReader
    monthly_work_accounts: TimeOfficeMonthlyWorkAccountReader
    demand: TimeOfficeDemandReader
    weights: TimeOfficeWeightsReader

    @classmethod
    def create(cls, *, facts: TimeOfficeFacts) -> "TimeOfficeReaders":
        return cls(
            options=TimeOfficeOptionsReader(facts=facts),
            planning_units=TimeOfficePlanningUnitReader(facts=facts),
            personnel=TimeOfficePersonnelReader(),
            shifts=TimeOfficeShiftReader(facts=facts),
            roster=TimeOfficeRosterReader(),
            wishes=TimeOfficeWishReader(),
            sunday_work_history=TimeOfficeSundayWorkHistoryReader(),
            monthly_work_accounts=TimeOfficeMonthlyWorkAccountReader(facts=facts),
            demand=TimeOfficeDemandReader(),
            weights=TimeOfficeWeightsReader(),
        )

    def read_sources(
        self,
        *,
        connection: Connection,
        selected_planning_unit_ids: tuple[int, ...],
        planning_month: PlanningMonth,
    ) -> TimeOfficeSources:
        planning_unit_rows = self.planning_units.read_rows(
            connection=connection,
            selected_planning_unit_ids=selected_planning_unit_ids,
            planning_month=planning_month,
        )

        plan_ids = tuple(row.plan_id for row in planning_unit_rows)
        planning_unit_ids = tuple(row.planning_unit_id for row in planning_unit_rows)

        plan_personnel_rows = self.personnel.read_plan_personnel_rows(
            connection=connection,
            plan_ids=plan_ids,
        )

        planning_unit_membership_rows = self.personnel.read_membership_rows(
            connection=connection,
            planning_unit_ids=planning_unit_ids,
            planning_month=planning_month,
        )

        employee_ids = _collect_relevant_employee_ids(
            plan_personnel_rows=plan_personnel_rows,
            planning_unit_membership_rows=planning_unit_membership_rows,
        )

        employee_rows = self.personnel.read_employee_rows(
            connection=connection,
            employee_ids=employee_ids,
        )

        shift_rows = self.shifts.read_rows(connection=connection)

        roster_rows = self.roster.read_rows(
            connection=connection,
            employee_ids=employee_ids,
            planning_month=planning_month,
        )

        wish_rows = self.wishes.read_rows(
            connection=connection,
            plan_ids=plan_ids,
            planning_unit_ids=planning_unit_ids,
            employee_ids=employee_ids,
            planning_month=planning_month,
        )

        sunday_history_rows = self.sunday_work_history.read_rows(
            connection=connection,
            employee_ids=employee_ids,
            planning_month=planning_month,
        )

        monthly_work_account_rows = self.monthly_work_accounts.read_rows(
            connection=connection,
            employee_ids=employee_ids,
            planning_month=planning_month,
        )

        demand_rows = self.demand.read_minimal_staffing(
            connection=connection,
            planning_unit_ids=planning_unit_ids,
        )

        objective_weight_rows = self.weights.read_rows(
            connection=connection,
            planning_unit_ids=planning_unit_ids,
        )

        return TimeOfficeSources(
            planning_unit_rows=planning_unit_rows,
            plan_personnel_rows=plan_personnel_rows,
            employee_rows=employee_rows,
            planning_unit_membership_rows=planning_unit_membership_rows,
            shift_rows=shift_rows,
            roster_rows=roster_rows,
            wish_rows=wish_rows,
            sunday_history_rows=sunday_history_rows,
            monthly_work_account_rows=monthly_work_account_rows,
            demand_rows=demand_rows,
            objective_weight_rows=objective_weight_rows,
        )


def _collect_relevant_employee_ids(
    *,
    plan_personnel_rows: tuple[TimeOfficePlanPersonnelRow, ...],
    planning_unit_membership_rows: tuple[TimeOfficePlanningUnitMembershipRow, ...],
) -> tuple[int, ...]:
    return tuple(
        dict.fromkeys(
            (
                *(row.employee_id for row in planning_unit_membership_rows),
                *(row.employee_id for row in plan_personnel_rows),
            )
        )
    )
