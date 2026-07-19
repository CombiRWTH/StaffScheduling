from sqlalchemy import Connection, text

from scheduling.domain import DemandRequirement
from scheduling.timeoffice.remapping.demand import (
    TimeOfficeMinimalStaffingWriteRow,
    map_demand_requirements_to_minimal_staffing_rows,
)


class TimeOfficeDemandWriter:
    def replace_minimal_staffing(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
        demand_requirements: tuple[DemandRequirement, ...],
    ) -> None:
        self._ensure_minimal_staffing_table_exists(connection=connection)

        rows = map_demand_requirements_to_minimal_staffing_rows(demand_requirements)

        self._delete_rows_for_planning_unit(
            connection=connection,
            planning_unit_id=planning_unit_id,
        )

        self._insert_rows(
            connection=connection,
            rows=rows,
        )

    def _delete_rows_for_planning_unit(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
    ) -> None:
        query = text(
            """
            DELETE FROM dbo.StaffSchedulingMinimalStaffing
            WHERE RefPlanungseinheiten = :planning_unit_id
            """
        )

        connection.execute(query, {"planning_unit_id": planning_unit_id})

    def _insert_rows(
        self,
        *,
        connection: Connection,
        rows: tuple[TimeOfficeMinimalStaffingWriteRow, ...],
    ) -> None:
        if not rows:
            return

        query = text(
            """
            INSERT INTO dbo.StaffSchedulingMinimalStaffing (
                RefPlanungseinheiten,
                WeekdayName,
                StaffLevel,
                RefDienste,
                MinimumCount
            )
            VALUES (
                :planning_unit_id,
                :weekday_name,
                :staff_level,
                :shift_id,
                :minimum_count
            )
            """
        )

        connection.execute(
            query,
            [
                {
                    "planning_unit_id": row.planning_unit_id,
                    "weekday_name": row.weekday_name,
                    "staff_level": row.staff_level,
                    "shift_id": row.shift_id,
                    "minimum_count": row.minimum_count,
                }
                for row in rows
            ],
        )

    def _ensure_minimal_staffing_table_exists(self, *, connection: Connection) -> None:
        query = text(
            """
            IF OBJECT_ID(N'dbo.StaffSchedulingMinimalStaffing', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.StaffSchedulingMinimalStaffing (
                    Id BIGINT IDENTITY(1,1) NOT NULL,

                    RefPlanungseinheiten INT NOT NULL,
                    WeekdayName NVARCHAR(16) NOT NULL,
                    StaffLevel NVARCHAR(32) NOT NULL,
                    RefDienste INT NOT NULL,
                    MinimumCount INT NOT NULL,

                    CONSTRAINT PK_StaffSchedulingMinimalStaffing
                        PRIMARY KEY (Id),

                    CONSTRAINT CK_StaffSchedulingMinimalStaffing_WeekdayName
                        CHECK (WeekdayName IN (
                            N'Montag',
                            N'Dienstag',
                            N'Mittwoch',
                            N'Donnerstag',
                            N'Freitag',
                            N'Samstag',
                            N'Sonntag'
                        )),

                    CONSTRAINT CK_StaffSchedulingMinimalStaffing_StaffLevel
                        CHECK (StaffLevel IN (
                            N'Fachkraft',
                            N'Hilfskraft',
                            N'Azubi'
                        )),

                    CONSTRAINT CK_StaffSchedulingMinimalStaffing_MinimumCount
                        CHECK (MinimumCount >= 0),

                    CONSTRAINT UQ_StaffSchedulingMinimalStaffing_BusinessKey
                        UNIQUE (
                            RefPlanungseinheiten,
                            WeekdayName,
                            StaffLevel,
                            RefDienste
                        )
                );
            END
            """
        )

        connection.execute(query)
