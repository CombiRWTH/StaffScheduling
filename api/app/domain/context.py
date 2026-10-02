"""Trusted facts around a planning month that its boundary rules need."""

from datetime import date as Date

from app.domain.assignment import Assignment
from app.domain.availability import Availability
from app.domain.core import SchedulingBaseModel


class ScheduleContext(SchedulingBaseModel):
    """Trusted duties outside the month and the approved availability its last duties can reach.

    Duties are complete from `covered_from` to `covered_until`, both inclusive: inside that span a
    date without a duty is known to be free, outside it nothing is known. The month itself is never
    context; `covered_from` equal to the month start means no preceding context, `covered_until`
    equal to the month end no following context. `availability` holds the first date after the month,
    which a night duty of the last date reaches. Context never counts towards demand or accounts.
    """

    covered_from: Date
    covered_until: Date
    duties: tuple[Assignment, ...] = ()
    availability: tuple[Availability, ...] = ()
