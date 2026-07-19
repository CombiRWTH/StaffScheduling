from sqlalchemy import Connection, text

from scheduling.domain import SolverObjectiveWeights
from scheduling.timeoffice.remapping.objective_weights import (
    TimeOfficeObjectiveWeightWriteRow,
    map_objective_weights_to_timeoffice_rows,
)


class TimeOfficeWeightsWriter:
    def replace_objective_weights(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
        objective_weights: SolverObjectiveWeights,
    ) -> None:
        if objective_weights.planning_unit_id != planning_unit_id:
            raise ValueError(
                "Objective weights planning_unit_id does not match target planning_unit_id: "
                f"objective_weights.planning_unit_id={objective_weights.planning_unit_id}, "
                f"planning_unit_id={planning_unit_id}."
            )

        self._ensure_objective_weights_table_exists(connection=connection)

        rows = map_objective_weights_to_timeoffice_rows(objective_weights)

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
            DELETE FROM dbo.StaffSchedulingObjectiveWeights
            WHERE RefPlanungseinheiten = :planning_unit_id
            """
        )

        connection.execute(query, {"planning_unit_id": planning_unit_id})

    def _insert_rows(
        self,
        *,
        connection: Connection,
        rows: tuple[TimeOfficeObjectiveWeightWriteRow, ...],
    ) -> None:
        if not rows:
            return

        query = text(
            """
            INSERT INTO dbo.StaffSchedulingObjectiveWeights (
                RefPlanungseinheiten,
                ObjectiveName,
                Weight
            )
            VALUES (
                :planning_unit_id,
                :objective_name,
                :weight
            )
            """
        )

        connection.execute(
            query,
            [
                {
                    "planning_unit_id": row.planning_unit_id,
                    "objective_name": row.objective_name,
                    "weight": row.weight,
                }
                for row in rows
            ],
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
