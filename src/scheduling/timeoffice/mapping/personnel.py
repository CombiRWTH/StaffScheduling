from scheduling.domain import Capability, Employee, PlanningUnitMembership, StaffLevel
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.reading.personnel import TimeOfficeEmployeeRow, TimeOfficePlanningUnitMembershipRow


def map_employees(rows: tuple[TimeOfficeEmployeeRow, ...], *, facts: TimeOfficeFacts) -> tuple[Employee, ...]:
    return tuple(
        Employee(
            employee_id=row.employee_id,
            display_name=_display_name(
                employee_id=row.employee_id,
                first_name=row.first_name,
                last_name=row.last_name,
            ),
            staff_level=_staff_level_from_profession(
                profession_id=row.employee_profession_id,
                profession_code=row.employee_profession_code,
                facts=facts,
                context=f"TPersonal employee_id={row.employee_id}",
            ),
            capabilities=_capabilities_for_employee(row.employee_id, facts=facts),
        )
        for row in rows
    )


def map_planning_unit_memberships(
    rows: tuple[TimeOfficePlanningUnitMembershipRow, ...], *, facts: TimeOfficeFacts
) -> tuple[PlanningUnitMembership, ...]:
    return tuple(
        PlanningUnitMembership(
            planning_unit_id=row.planning_unit_id,
            employee_id=row.employee_id,
            valid_from=row.valid_from.date(),
            valid_until=row.valid_until.date() if row.valid_until is not None else None,
            staff_level=_staff_level_from_profession(
                profession_id=row.membership_profession_id,
                profession_code=row.membership_profession_code,
                facts=facts,
                context=(
                    f"TPlanungseinheitenPersonal planning_unit_id={row.planning_unit_id} employee_id={row.employee_id}"
                ),
            ),
            is_home=row.is_home,
            is_replacement=row.is_replacement,
        )
        for row in rows
    )


def _staff_level_from_profession(
    *,
    profession_id: int,
    profession_code: str | None,
    facts: TimeOfficeFacts,
    context: str,
) -> StaffLevel:
    if profession_code is None:
        raise ValueError(f"Missing TimeOffice profession code: context={context} profession_id={profession_id}.")

    staff_level = facts.staff_level_by_profession_code.get(profession_code)

    if staff_level is None:
        known_codes = ", ".join(sorted(facts.staff_level_by_profession_code))
        raise ValueError(
            "No StaffLevel mapping configured for TimeOffice profession: "
            f"context={context} "
            f"profession_id={profession_id} "
            f"profession_code={profession_code!r}. "
            f"Known profession_codes=[{known_codes}]."
        )

    return staff_level


def _capabilities_for_employee(employee_id: int, *, facts: TimeOfficeFacts) -> tuple[Capability, ...]:
    return tuple(facts.capabilities_by_employee_id.get(employee_id, ()))


def _display_name(
    *,
    employee_id: int,
    first_name: str | None,
    last_name: str | None,
) -> str:
    display_name = " ".join(part for part in (last_name, first_name) if part)
    return display_name or f"Employee {employee_id}"
