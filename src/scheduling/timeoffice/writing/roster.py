from datetime import date as Date

from sqlalchemy import Connection, text

from scheduling.domain import Availability, PlanningMonth
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.remapping.roster import (
    TimeOfficeAvailabilityWriteRow,
    map_availabilities_to_timeoffice_rows,
)

WEB_AVAILABILITY_INFO = "StaffSchedulingWebAvailability"


class TimeOfficeAvailabilityWriter:
    def replace_employee_availability(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
        planning_month: PlanningMonth,
        employee_id: int,
        availabilities: tuple[Availability, ...],
        facts: TimeOfficeFacts,
    ) -> None:
        plan_id = self._find_target_plan_id(
            connection=connection,
            planning_unit_id=planning_unit_id,
            planning_month=planning_month,
        )

        self._delete_web_availability_rows(
            connection=connection,
            planning_unit_id=planning_unit_id,
            planning_month=planning_month,
            employee_id=employee_id,
        )

        rows = map_availabilities_to_timeoffice_rows(
            availabilities=availabilities,
            plan_id=plan_id,
            planning_unit_id=planning_unit_id,
            facts=facts,
        )

        self._insert_rows(
            connection=connection,
            rows=rows,
            facts=facts,
        )

    def _delete_web_availability_rows(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
        planning_month: PlanningMonth,
        employee_id: int,
    ) -> None:
        query = text(
            """
            DELETE FROM TPlanPersonalKommtGeht
            WHERE RefPersonal = :employee_id
              AND RefPlanungseinheiten = :planning_unit_id
              AND CONVERT(date, Datum) BETWEEN :start AND :end
              AND Info = :info
            """
        )

        connection.execute(
            query,
            {
                "employee_id": employee_id,
                "planning_unit_id": planning_unit_id,
                "start": planning_month.start,
                "end": planning_month.end,
                "info": WEB_AVAILABILITY_INFO,
            },
        )

    def _insert_rows(
        self,
        *,
        connection: Connection,
        rows: tuple[TimeOfficeAvailabilityWriteRow, ...],
        facts: TimeOfficeFacts,
    ) -> None:
        if not rows:
            return

        query = text(
            """
            INSERT INTO TPlanPersonalKommtGeht (
                RefPlan,
                RefPersonal,
                Datum,
                RefStati,
                lfdNr,
                RefgAbw,
                RefDienste,
                RefBerufe,
                RefPlanungseinheiten,
                VonZeit,
                BisZeit,
                RefDienstAbw,
                Minuten,
                Info,
                RefEinsatzArten,
                Wunschdienst,
                BereitVon,
                BereitBis
            )
            VALUES (
                :plan_id,
                :employee_id,
                :availability_date,
                :status_id,
                :sequence_number,
                NULL,
                :work_shift_id,
                :profession_id,
                :planning_unit_id,
                NULL,
                NULL,
                :absence_shift_id,
                0,
                :info,
                NULL,
                0,
                NULL,
                NULL
            )
            """
        )

        connection.execute(
            query,
            self._insert_parameters(
                connection=connection,
                rows=rows,
                facts=facts,
            ),
        )

    def _insert_parameters(
        self,
        *,
        connection: Connection,
        rows: tuple[TimeOfficeAvailabilityWriteRow, ...],
        facts: TimeOfficeFacts,
    ) -> list[dict[str, object]]:
        next_sequence_by_key: dict[tuple[int, int, Date], int] = {}

        parameters: list[dict[str, object]] = []

        for row in rows:
            sequence_key = (
                row.plan_id,
                row.employee_id,
                row.availability_date,
            )

            if sequence_key not in next_sequence_by_key:
                next_sequence_by_key[sequence_key] = self._next_sequence_number(
                    connection=connection,
                    plan_id=row.plan_id,
                    employee_id=row.employee_id,
                    date_value=row.availability_date,
                )

            sequence_number = next_sequence_by_key[sequence_key]
            next_sequence_by_key[sequence_key] += 1

            parameters.append(
                {
                    "plan_id": row.plan_id,
                    "employee_id": row.employee_id,
                    "availability_date": row.availability_date,
                    "status_id": facts.target_planning_status_id,
                    "sequence_number": sequence_number,
                    "work_shift_id": row.work_shift_id,
                    "profession_id": self._find_profession_id(
                        connection=connection,
                        employee_id=row.employee_id,
                        planning_unit_id=row.planning_unit_id,
                    ),
                    "planning_unit_id": row.planning_unit_id,
                    "absence_shift_id": row.absence_shift_id,
                    "info": WEB_AVAILABILITY_INFO,
                }
            )

        return parameters

    def _find_target_plan_id(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
        planning_month: PlanningMonth,
    ) -> int:
        query = text(
            """
            SELECT TOP 1
                pkg.RefPlan AS plan_id,
                COUNT(*) AS row_count
            FROM TPlanPersonalKommtGeht pkg
            WHERE pkg.RefPlanungseinheiten = :planning_unit_id
              AND CONVERT(date, pkg.Datum) BETWEEN :start AND :end
            GROUP BY pkg.RefPlan
            ORDER BY row_count DESC
            """
        )

        row = (
            connection.execute(
                query,
                {
                    "planning_unit_id": planning_unit_id,
                    "start": planning_month.start,
                    "end": planning_month.end,
                },
            )
            .mappings()
            .first()
        )

        if row is None:
            raise ValueError(
                f"No TimeOffice plan found for planning_unit_id={planning_unit_id}, "
                f"planning_month={planning_month.label}."
            )

        return int(row["plan_id"])

    def _next_sequence_number(
        self,
        *,
        connection: Connection,
        plan_id: int,
        employee_id: int,
        date_value: object,
    ) -> int:
        query = text(
            """
            SELECT COALESCE(MAX(pkg.lfdNr), 0) + 1 AS next_sequence_number
            FROM TPlanPersonalKommtGeht pkg
            WHERE pkg.RefPlan = :plan_id
              AND pkg.RefPersonal = :employee_id
              AND CONVERT(date, pkg.Datum) = :date_value
            """
        )

        row = (
            connection.execute(
                query,
                {
                    "plan_id": plan_id,
                    "employee_id": employee_id,
                    "date_value": date_value,
                },
            )
            .mappings()
            .one()
        )

        return int(row["next_sequence_number"])

    def _find_profession_id(
        self,
        *,
        connection: Connection,
        employee_id: int,
        planning_unit_id: int,
    ) -> int:
        query = text(
            """
            SELECT TOP 1
                pkg.RefBerufe AS profession_id,
                COUNT(*) AS usage_count
            FROM TPlanPersonalKommtGeht pkg
            WHERE pkg.RefPersonal = :employee_id
              AND pkg.RefPlanungseinheiten = :planning_unit_id
              AND pkg.RefBerufe IS NOT NULL
            GROUP BY pkg.RefBerufe
            ORDER BY usage_count DESC
            """
        )

        row = (
            connection.execute(
                query,
                {
                    "employee_id": employee_id,
                    "planning_unit_id": planning_unit_id,
                },
            )
            .mappings()
            .first()
        )

        if row is None:
            raise ValueError(
                f"No TimeOffice profession found for employee_id={employee_id}, planning_unit_id={planning_unit_id}."
            )

        return int(row["profession_id"])

    def delete_employee_availability(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
        planning_month: PlanningMonth,
        employee_id: int,
    ) -> None:
        self._delete_web_availability_rows(
            connection=connection,
            planning_unit_id=planning_unit_id,
            planning_month=planning_month,
            employee_id=employee_id,
        )
