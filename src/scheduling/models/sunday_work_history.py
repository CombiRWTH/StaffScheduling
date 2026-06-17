from pydantic import Field

from scheduling.models.core import SchedulingBaseModel
from scheduling.models.employee import EmployeeId


class EmployeeSundayWorkHistory(SchedulingBaseModel):
    """Historical Sunday workload for one employee in the configured lookback window."""

    employee_id: EmployeeId
    worked_sundays: int = Field(ge=0)
