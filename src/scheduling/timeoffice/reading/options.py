from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection

from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.reading.types import CleanNullableText, SourceInt, TimeOfficeSourceRow


class TimeOfficePlanningUnitOptionRow(TimeOfficeSourceRow):
    planning_unit_id: SourceInt
    planning_unit_code: CleanNullableText = None


class TimeOfficeOptionsReader:
    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def read_planning_unit_option_rows(
        self,
        *,
        connection: Connection,
    ) -> tuple[TimeOfficePlanningUnitOptionRow, ...]:
        planning_unit_ids = tuple(sorted(self._facts.planning_unit_type_by_id))

        if not planning_unit_ids:
            return ()

        query = text(
            """
            SELECT
                pe.Prim AS planning_unit_id,
                pe.KurzBez AS planning_unit_code
            FROM TPlanungseinheiten pe
            WHERE pe.Prim IN :planning_unit_ids
            ORDER BY
                pe.Prim
            """
        ).bindparams(bindparam("planning_unit_ids", expanding=True))

        raw_rows = (
            connection.execute(
                query,
                {"planning_unit_ids": planning_unit_ids},
            )
            .mappings()
            .all()
        )

        return tuple(TimeOfficePlanningUnitOptionRow.model_validate(row) for row in raw_rows)
