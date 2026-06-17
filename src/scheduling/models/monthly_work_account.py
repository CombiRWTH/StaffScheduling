from pydantic import NonNegativeInt

from scheduling.models.core import SchedulingBaseModel
from scheduling.models.employee import EmployeeId


class MonthlyWorkAccount(SchedulingBaseModel):
    employee_id: EmployeeId
    target_minutes: NonNegativeInt
    actual_minutes: NonNegativeInt | None = None
