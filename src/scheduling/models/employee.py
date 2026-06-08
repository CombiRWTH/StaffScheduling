from pydantic import BaseModel, Field


class Employee(BaseModel):
    """Employee identity and stable staffing classification.

    Period-specific facts like availability, assignments, wishes, and station
    memberships are represented as separate relationship records.
    """

    employee_id: int = Field(gt=0)
    personnel_number: str | None = None

    first_name: str | None = None
    last_name: str | None = None
    display_name: str

    group_id: str | None = None
    active: bool = True
