from pydantic import Json
from sqlalchemy import Connection, bindparam, text

from app.domain import Availability, NonEmptyStr, PlanningMonth
from app.domain.monthly_work_account import WorkCredit
from app.employees.models import EmployeeMonthEvidence
from app.timeoffice.reading.types import SourceInt, TimeOfficeSourceRow


class EmployeeMonthEvidenceRow(TimeOfficeSourceRow):
    employee_id: SourceInt
    credit_details: Json[tuple[WorkCredit, ...]]
    hard_restrictions: Json[tuple[Availability, ...]]
    source: NonEmptyStr


def read_employee_evidence(
    *, connection: Connection, employee_ids: tuple[int, ...], planning_month: PlanningMonth
) -> tuple[EmployeeMonthEvidence, ...]:
    """Read explicitly prepared evidence; never provision storage on a read."""
    if not employee_ids:
        return ()
    query = text(
        """
        SELECT employee_id, credit_details, hard_restrictions, source
        FROM dbo.StaffSchedulingEmployeeMonthEvidence
        WHERE employee_id IN :employee_ids AND planning_month = :planning_month
        ORDER BY employee_id
        """
    ).bindparams(bindparam("employee_ids", expanding=True))
    rows = (
        connection.execute(query, {"employee_ids": employee_ids, "planning_month": planning_month.start})
        .mappings()
        .all()
    )
    return tuple(
        EmployeeMonthEvidence.model_validate(EmployeeMonthEvidenceRow.model_validate(row).model_dump()) for row in rows
    )
