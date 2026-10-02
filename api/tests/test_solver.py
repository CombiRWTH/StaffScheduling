"""Production solves of small months: every hard rule is modelled, the objective tiers keep their order."""

from datetime import date

import pytest
from scheduling import (
    EARLY,
    INTERMEDIATE,
    JANUARY,
    JUMPER_POOL,
    LATE,
    NIGHT,
    NORTH,
    SOUTH,
    account,
    away,
    dataset,
    duty,
    jan,
    member,
    need,
)

from app.domain import (
    Assignment,
    Availability,
    AvailabilityType,
    CheckStatus,
    PlanningMonth,
    ScheduleCheck,
    ScheduleScores,
    SchedulingDataset,
    StaffLevel,
    check_schedule,
)
from app.settings import Settings
from app.solver.model.objectives import OBJECTIVES
from app.solver.models import ObjectiveWeights, Solution, SolutionStatus
from app.solver.service import SolverService

pytestmark = pytest.mark.integration

SOLVER = SolverService(Settings(solver_num_search_workers=1, solver_random_seed=1))


def solve(data: SchedulingDataset) -> Solution:
    return SOLVER.solve(data, timeout=20)


def checked(solution: Solution) -> ScheduleCheck:
    assert solution.check is not None
    return solution.check


def objective(solution: Solution) -> int:
    assert solution.objective is not None
    return solution.objective.value


def weighted_total(solution: Solution) -> int:
    scores, weights = checked(solution).scores, solution.configuration.weights
    return (
        weights.health_events * scores.health_events
        + weights.balance_deviation_minutes * scores.balance_deviation_minutes
        - weights.surplus_intermediate_duties * scores.surplus_intermediate_duties
    )


def only(employee_id: int, allowed: dict[int, tuple[int, ...]]) -> list[Availability]:
    """Unavailable on every January date except the given ones, which allow only the listed shifts."""
    return [
        away(employee_id, day, AvailabilityType.AVAILABLE_ONLY, allowed[day.day])
        if day.day in allowed
        else away(employee_id, day, AvailabilityType.UNAVAILABLE)
        for day in JANUARY.dates
    ]


def test_objective_tiers_are_the_reported_weights_and_scores_in_priority_order() -> None:
    names = [tier.name for tier in OBJECTIVES]
    assert names == list(ObjectiveWeights.model_fields)
    assert set(names) <= set(ScheduleScores.model_fields) | set(ScheduleScores.model_computed_fields)


def test_a_solved_month_is_accepted_and_its_objective_is_the_checked_weighted_total() -> None:
    weekdays = [jan(day) for day in range(5, 10)]
    data = dataset(
        memberships=[
            *member(1),
            *member(2),
            *member(3, StaffLevel.ASSISTANT, home=JUMPER_POOL, replacements=[NORTH, SOUTH]),
        ],
        accounts=[account(1, 5 * 420), account(2, 5 * 435), account(3, 420)],
        demand=[
            *(need(day, EARLY) for day in weekdays),
            *(need(day, LATE) for day in weekdays),
            need(jan(6), EARLY, level=StaffLevel.ASSISTANT, unit=SOUTH),
        ],
    )
    solution = solve(data)

    assert solution.status == SolutionStatus.OPTIMAL
    assert checked(solution).status == CheckStatus.ACCEPTED
    assert solution.objective is not None
    assert objective(solution) == weighted_total(solution) == round(solution.objective.best_bound)
    # The jumper pool employee is credited as the assistant their station membership makes them.
    assert duty(3, jan(6), EARLY, unit=SOUTH, level=StaffLevel.ASSISTANT) in solution.assignments
    # The check is independent: removing a duty the model needed is caught.
    assert check_schedule(data, solution.assignments[1:]).status == CheckStatus.REJECTED


def test_trusted_context_constrains_the_first_days_of_the_month() -> None:
    december_nights = [duty(1, date(2025, 12, day), NIGHT) for day in (29, 30, 31)]
    data = dataset(
        memberships=[*member(1), *member(2)],
        accounts=[account(1, 0), account(2, 555)],
        demand=[need(jan(1), NIGHT)],
        context_duties=december_nights,
    )
    solution = solve(data)

    # A fourth night in a row is not allowed, so the other employee takes January 1.
    assert checked(solution).status == CheckStatus.ACCEPTED
    assert [row for row in solution.assignments if row.date == jan(1)] == [duty(2, jan(1), NIGHT)]


def test_unmet_demand_is_infeasible_and_diagnosed() -> None:
    data = dataset(
        memberships=[*member(1, StaffLevel.MFA), *member(2, StaffLevel.ASSISTANT)],
        accounts=[account(1, 420), account(2, 0)],
        demand=[need(jan(5), EARLY, count=2, level=StaffLevel.MFA)],
    )
    solution = solve(data)

    assert solution.status == SolutionStatus.INFEASIBLE
    assert (solution.assignments, solution.check, solution.objective) == ((), None, None)
    assert [row.code for row in solution.diagnostics] == ["staffing.too_few_candidates"]


def test_a_jumper_pool_employee_cannot_fill_both_stations_on_one_date() -> None:
    data = dataset(
        memberships=member(1, StaffLevel.ASSISTANT, home=JUMPER_POOL, replacements=[NORTH, SOUTH]),
        accounts=[account(1, 840)],
        demand=[need(jan(5), EARLY, level=StaffLevel.ASSISTANT, unit=unit) for unit in (NORTH, SOUTH)],
    )
    assert solve(data).status == SolutionStatus.INFEASIBLE


def test_a_month_needs_every_account_before_it_solves() -> None:
    memberships = [*member(1), *member(2)]
    with pytest.raises(ValueError, match="exactly one monthly account"):
        dataset(memberships=memberships, accounts=[account(1, 0)])
    assert solve(dataset(memberships=memberships, accounts=[account(1, 0), account(2, 0)])).status == (
        SolutionStatus.OPTIMAL
    )


def test_the_night_before_the_october_clock_change_is_never_assigned() -> None:
    # The repeated hour stretches the night's last segment of 00:30-06:10 to 6 h 40 min without a break.
    october = PlanningMonth(year=2026, month=10)
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 555, month=october)],
        demand=[need(date(2026, 10, 24), NIGHT)],
        month=october,
    )
    solution = solve(data)

    assert solution.status == SolutionStatus.INFEASIBLE
    assert {row.code for row in solution.diagnostics} >= {"shift.breaks_rules", "staffing.too_few_candidates"}


@pytest.mark.parametrize(("target", "status"), [(1000, SolutionStatus.INFEASIBLE), (400, SolutionStatus.OPTIMAL)])
def test_employees_without_possible_duties_still_need_a_balanced_account(target: int, status: SolutionStatus) -> None:
    data = dataset(
        memberships=[*member(1), *member(2, home=JUMPER_POOL)],
        accounts=[account(1, 0), account(2, target)],
    )
    solution = solve(data)

    assert solution.status == status
    assert ("balance.unreachable" in [row.code for row in solution.diagnostics]) == (
        status == SolutionStatus.INFEASIBLE
    )


@pytest.mark.parametrize(("extra_late_day", "worked"), [(8, False), (11, True)])
def test_health_events_outweigh_the_monthly_balance(extra_late_day: int, worked: bool) -> None:
    # The required early of January 10 leaves a late short of the target. A late on January 8 would
    # step back from late to early; one on January 11 steps forward.
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 420 + 435)],
        demand=[need(jan(10), EARLY)],
        availability=only(1, {10: (EARLY.shift_id,), extra_late_day: (LATE.shift_id,)}),
    )
    solution = solve(data)

    assert checked(solution).status == CheckStatus.ACCEPTED
    assert (duty(1, jan(extra_late_day), LATE) in solution.assignments) == worked
    assert checked(solution).scores.backward_transitions == 0
    assert checked(solution).scores.balance_deviation_minutes == (0 if worked else 435)
    assert objective(solution) == weighted_total(solution)


@pytest.mark.parametrize(("short_by", "intermediate"), [(172, False), (173, True)])
def test_the_balance_outweighs_extra_intermediate_duties(short_by: int, intermediate: bool) -> None:
    # An optional 345-minute intermediate duty helps only if it brings the balance closer, by even one minute.
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 420 + short_by)],
        demand=[need(jan(10), EARLY)],
        availability=only(1, {10: (EARLY.shift_id,), 12: (INTERMEDIATE.shift_id,)}),
    )
    solution = solve(data)
    extra: Assignment = duty(1, jan(12), INTERMEDIATE)

    assert (extra in solution.assignments) == intermediate
    assert checked(solution).scores.surplus_intermediate_duties == int(intermediate)
    assert objective(solution) == weighted_total(solution)
