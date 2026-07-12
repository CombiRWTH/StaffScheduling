from sqlalchemy import Connection, bindparam, text

from scheduling.domain.core import SchedulingBaseModel


class TimeOfficeObjectiveWeightRow(SchedulingBaseModel):
    planning_unit_id: int
    objective_name: str
    weight: int


class TimeOfficeWeightsReader:
    def read_rows(
        self,
        *,
        connection: Connection,
        planning_unit_ids: tuple[int, ...],
    ) -> tuple[TimeOfficeObjectiveWeightRow, ...]:
        self._ensure_objective_weights_table_exists(connection=connection)

        if not planning_unit_ids:
            return ()

        query = text(
            """
                SELECT
                    RefPlanungseinheiten AS planning_unit_id,
                    ObjectiveName AS objective_name,
                    Weight AS weight
                FROM dbo.StaffSchedulingObjectiveWeights
                WHERE RefPlanungseinheiten IN :planning_unit_ids
                """
        ).bindparams(bindparam("planning_unit_ids", expanding=True))

        rows = connection.execute(
            query,
            {"planning_unit_ids": planning_unit_ids},
        ).mappings()

        return tuple(
            TimeOfficeObjectiveWeightRow(
                planning_unit_id=int(row["planning_unit_id"]),
                objective_name=str(row["objective_name"]),
                weight=int(row["weight"]),
            )
            for row in rows
        )

    def _ensure_objective_weights_table_exists(self, *, connection: Connection) -> None:
        query = text(
            """
            IF OBJECT_ID(N'dbo.StaffSchedulingObjectiveWeights', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.StaffSchedulingObjectiveWeights (
                    Id BIGINT IDENTITY(1,1) NOT NULL,

                    RefPlanungseinheiten INT NOT NULL,
                    ObjectiveName NVARCHAR(80) NOT NULL,
                    Weight INT NOT NULL,

                    CONSTRAINT PK_StaffSchedulingObjectiveWeights
                        PRIMARY KEY (Id),

                    CONSTRAINT CK_StaffSchedulingObjectiveWeights_ObjectiveName
                        CHECK (ObjectiveName IN (
                            N'recovery_after_night_shift',
                            N'consecutive_working_days',
                            N'consecutive_night_shifts',
                            N'fairness',
                            N'free_weekend',
                            N'hidden_employee',
                            N'overtime_penalty',
                            N'shift_rotation',
                            N'second_weekend_penalty',
                            N'employee_wish'
                        )),

                    CONSTRAINT CK_StaffSchedulingObjectiveWeights_Weight
                        CHECK (Weight >= 0),

                    CONSTRAINT UQ_StaffSchedulingObjectiveWeights_BusinessKey
                        UNIQUE (
                            RefPlanungseinheiten,
                            ObjectiveName
                        )
                );
            END
            """
        )

        connection.execute(query)
