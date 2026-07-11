from sqlalchemy import Connection, bindparam, text

from scheduling.domain.core import SchedulingBaseModel


class TimeOfficeDemandRow(SchedulingBaseModel):
    planning_unit_id: int
    weekday_name: str
    staff_level: str
    shift_id: int
    minimum_count: int


class TimeOfficeDemandReader:
    def read_minimal_staffing(
        self,
        *,
        connection: Connection,
        planning_unit_ids: tuple[int, ...],
    ) -> tuple[TimeOfficeDemandRow, ...]:
        self._ensure_minimal_staffing_table_exists(connection=connection)

        if not planning_unit_ids:
            return ()

        query = text(
            """
                SELECT
                    RefPlanungseinheiten AS planning_unit_id,
                    WeekdayName AS weekday_name,
                    StaffLevel AS staff_level,
                    RefDienste AS shift_id,
                    MinimumCount AS minimum_count
                FROM dbo.StaffSchedulingMinimalStaffing
                WHERE RefPlanungseinheiten IN :planning_unit_ids
                """
        ).bindparams(bindparam("planning_unit_ids", expanding=True))

        rows = connection.execute(
            query,
            {"planning_unit_ids": planning_unit_ids},
        ).mappings()

        return tuple(
            TimeOfficeDemandRow(
                planning_unit_id=int(row["planning_unit_id"]),
                weekday_name=str(row["weekday_name"]),
                staff_level=str(row["staff_level"]),
                shift_id=int(row["shift_id"]),
                minimum_count=int(row["minimum_count"]),
            )
            for row in rows
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
