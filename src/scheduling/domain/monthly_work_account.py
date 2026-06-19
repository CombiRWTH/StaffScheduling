from pydantic import NonNegativeInt

from scheduling.domain.core import SchedulingBaseModel
from scheduling.domain.employee import EmployeeId


class MonthlyWorkAccount(SchedulingBaseModel):
    employee_id: EmployeeId
    target_minutes: NonNegativeInt
    actual_minutes: NonNegativeInt | None = None
