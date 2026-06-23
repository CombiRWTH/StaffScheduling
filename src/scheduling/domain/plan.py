from scheduling.domain.core import PositiveId, SchedulingBaseModel
from scheduling.domain.planning_unit import PlanningUnitId

PlanId = PositiveId


class Plan(SchedulingBaseModel):
    """Concrete selected TimeOffice plan for one PlanningUnit.

    Plan is kept as write-back context. It should stay minimal: the repository
    already selected the correct interval/status using TimeOfficeFacts.
    """

    plan_id: PlanId
    planning_unit_id: PlanningUnitId
