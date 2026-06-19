from scheduling.domain import SchedulingBaseModel


class SolverResult(SchedulingBaseModel):
    status: str
    message: str
    assignments_created: int = 0
