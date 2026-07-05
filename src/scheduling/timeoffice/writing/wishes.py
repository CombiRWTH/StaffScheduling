from sqlalchemy import Connection, text

from scheduling.domain import PlanningMonth, Wish
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.remapping.wishes import TimeOfficeWishWriteRow, map_wishes_to_timeoffice_rows


class TimeOfficeWishWriter:
    def __init__(self, *, target_planning_status_id: int) -> None:
        self._target_planning_status_id = target_planning_status_id

    def insert_wishes(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
        planning_month: PlanningMonth,
        wishes: tuple[Wish, ...],
        facts: TimeOfficeFacts,
    ) -> None:
        if not wishes:
            return

        plan_id = self._find_target_plan_id(
            connection=connection,
            planning_unit_id=planning_unit_id,
            planning_month=planning_month,
        )

        rows = map_wishes_to_timeoffice_rows(
            wishes=wishes,
            plan_id=plan_id,
            facts=facts,
        )

        self._insert_rows(connection=connection, rows=rows)

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
                "No TimeOffice target plan found for wishes: "
                f"planning_unit_id={planning_unit_id} "
                f"planning_month={planning_month.label}."
            )

        return int(row["plan_id"])

    def _insert_rows(
        self,
        *,
        connection: Connection,
        rows: tuple[TimeOfficeWishWriteRow, ...],
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
                :wish_date,
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
                NULL,
                NULL,
                1,
                NULL,
                NULL
            )
            """
        )

        sequence_numbers: dict[tuple[int, int, object], int] = {}

        def next_sequence_number(row: TimeOfficeWishWriteRow) -> int:
            key = (row.plan_id, row.employee_id, row.wish_date)

            if key not in sequence_numbers:
                sequence_numbers[key] = self._next_sequence_number(
                    connection=connection,
                    plan_id=row.plan_id,
                    employee_id=row.employee_id,
                    wish_date=row.wish_date,
                )

            sequence_number = sequence_numbers[key]
            sequence_numbers[key] += 1
            return sequence_number

        connection.execute(
            query,
            [
                {
                    "plan_id": row.plan_id,
                    "employee_id": row.employee_id,
                    "wish_date": row.wish_date,
                    "status_id": self._target_planning_status_id,
                    "sequence_number": next_sequence_number(row),
                    "work_shift_id": row.work_shift_id,
                    "profession_id": self._find_profession_id(
                        connection=connection,
                        employee_id=row.employee_id,
                        planning_unit_id=row.planning_unit_id,
                    ),
                    "planning_unit_id": row.planning_unit_id,
                    "absence_shift_id": row.absence_shift_id,
                }
                for row in rows
            ],
        )

    def _next_sequence_number(
        self,
        *,
        connection: Connection,
        plan_id: int,
        employee_id: int,
        wish_date: object,
    ) -> int:
        query = text(
            """
            SELECT
                COALESCE(MAX(pkg.lfdNr), 0) + 1 AS next_sequence_number
            FROM TPlanPersonalKommtGeht pkg
            WHERE pkg.RefPlan = :plan_id
                AND pkg.RefPersonal = :employee_id
                AND CONVERT(date, pkg.Datum) = :wish_date
            """
        )

        row = (
            connection.execute(
                query,
                {
                    "plan_id": plan_id,
                    "employee_id": employee_id,
                    "wish_date": wish_date,
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
                "No TimeOffice profession found for employee wishes: "
                f"employee_id={employee_id} "
                f"planning_unit_id={planning_unit_id}."
            )

        return int(row["profession_id"])

    def delete_employee_wishes(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
        planning_month: PlanningMonth,
        employee_id: int,
    ) -> None:
        plan_id = self._find_target_plan_id(
            connection=connection,
            planning_unit_id=planning_unit_id,
            planning_month=planning_month,
        )

        query = text(
            """
            DELETE FROM TPlanPersonalKommtGeht
            WHERE RefPlan = :plan_id
                AND RefPersonal = :employee_id
                AND RefPlanungseinheiten = :planning_unit_id
                AND CONVERT(date, Datum) BETWEEN :start AND :end
                AND ISNULL(Wunschdienst, 0) <> 0
                AND (
                    RefDienste IS NOT NULL
                    OR RefgAbw IS NOT NULL
                    OR RefDienstAbw IS NOT NULL
                )
            """
        )

        connection.execute(
            query,
            {
                "plan_id": plan_id,
                "employee_id": employee_id,
                "planning_unit_id": planning_unit_id,
                "start": planning_month.start,
                "end": planning_month.end,
            },
        )
