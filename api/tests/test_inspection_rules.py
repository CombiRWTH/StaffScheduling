from datetime import date

from app.domain import PlanningUnitMembership, StaffLevel, inspection_employee_ids


def membership(employee_id: int, unit_id: int, *, home: bool) -> PlanningUnitMembership:
    return PlanningUnitMembership(
        planning_unit_id=unit_id,
        employee_id=employee_id,
        valid_from=date(2026, 1, 1),
        staff_level=StaffLevel.PROFESSIONAL,
        is_home=home,
        is_replacement=not home,
    )


def test_scope_adds_only_pools_that_station_members_call_home() -> None:
    memberships = [
        membership(1, 201, home=True),  # pool origin of a station member
        membership(1, 101, home=False),
        membership(2, 101, home=True),
        membership(2, 202, home=False),  # replacement in a pool does not associate it
        membership(3, 201, home=True),  # other member of the associated pool
        membership(4, 202, home=True),  # member of an unassociated pool
        membership(5, 103, home=True),  # unselected station
    ]

    assert inspection_employee_ids(
        selected_station_ids=(101,), memberships=memberships, jumper_pool_ids={201, 202}
    ) == {1, 2, 3}


def test_scope_without_station_members_is_empty() -> None:
    memberships = [membership(3, 201, home=True)]

    assert inspection_employee_ids(selected_station_ids=(101,), memberships=memberships, jumper_pool_ids={201}) == set()
