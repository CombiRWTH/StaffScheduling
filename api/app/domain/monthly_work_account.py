from pydantic import NonNegativeInt

from app.domain.core import SchedulingBaseModel
from app.domain.employee import EmployeeId


class MonthlyWorkAccount(SchedulingBaseModel):
    employee_id: EmployeeId
    target_minutes: NonNegativeInt
    actual_minutes: NonNegativeInt | None = None
