"""Production solves of small months: every hard rule is modelled, the objective stages keep their order."""

from datetime import date
from typing import Any

import pytest
from ortools.sat.python import cp_model
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
    Gap,
    PlanningMonth,
    ScheduleCheck,
    ScheduleScores,
    SchedulingDataset,
    Shift,
    StaffLevel,
    Wish,
    WishStatus,
    WishType,
    check_schedule,
)
from app.settings import Settings
from app.solver.diagnostics import DiagnosticSeverity
from app.solver.model.objectives import OBJECTIVES
from app.solver.models import Solution, SolutionStatus
from app.solver.service import SolverService

pytestmark = pytest.mark.integration

SOLVER = SolverService(Settings(solver_num_search_workers=1, solver_random_seed=1))


def solve(data: SchedulingDataset) -> Solution:
    return SOLVER.solve(data, timeout=20)


def checked(solution: Solution) -> ScheduleCheck:
    assert solution.check is not None
    return solution.check


def stages_are_scores(solution: Solution) -> bool:
    """Whether every stage, in tier order, reports the checked score of its tier."""
    scores = checked(solution).scores
    return [(stage.name, stage.value) for stage in solution.stages] == [
        (tier.name, getattr(scores, tier.name)) for tier in OBJECTIVES
    ]


def only(employee_id: int, allowed: dict[int, tuple[int, ...]]) -> list[Availability]:
    """Unavailable on every January date except the given ones, which allow only the listed shifts."""
    return [
        away(employee_id, day, AvailabilityType.AVAILABLE_ONLY, allowed[day.day])
        if day.day in allowed
        else away(employee_id, day, AvailabilityType.UNAVAILABLE)
        for day in JANUARY.dates
    ]


def test_objective_tiers_are_checked_scores() -> None:
    names = [tier.name for tier in OBJECTIVES]
    assert len(set(names)) == len(names)
    assert set(names) <= set(ScheduleScores.model_fields) | set(ScheduleScores.model_computed_fields)


def test_a_solved_month_is_accepted_and_every_stage_is_its_checked_score() -> None:
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
    assert stages_are_scores(solution)
    assert all(stage.status == SolutionStatus.OPTIMAL for stage in solution.stages)
    assert all(stage.value == round(stage.best_bound) for stage in solution.stages)
    # The jumper pool employee is credited as the assistant their station membership makes them.
    assert duty(3, jan(6), EARLY, unit=SOUTH, level=StaffLevel.ASSISTANT) in solution.assignments
    # The check is independent: removing a duty the model needed is caught.
    assert check_schedule(data, solution.assignments[1:]).status == CheckStatus.REJECTED


def test_a_later_stage_without_time_keeps_the_previous_schedule_as_feasible(monkeypatch: pytest.MonkeyPatch) -> None:
    budgets: list[float] = []

    class FirstStageOnly(cp_model.CpSolver):
        def solve(
            self, model: cp_model.CpModel, solution_callback: cp_model.CpSolverSolutionCallback | None = None
        ) -> Any:
            budgets.append(self.parameters.max_time_in_seconds)
            if len(budgets) > 1:
                self.parameters.max_time_in_seconds = 0
            return super().solve(model, solution_callback)

    monkeypatch.setattr(cp_model, "CpSolver", FirstStageOnly)
    data = dataset(
        memberships=[*member(1), *member(2)],
        accounts=[account(1, 5 * 420), account(2, 5 * 435)],
        demand=[need(jan(day), shift_) for day in range(5, 10) for shift_ in (EARLY, LATE)],
    )
    solution = SOLVER.solve(data, timeout=30)

    # Each stage gets the time left divided by the stages left.
    assert budgets[0] == pytest.approx(30 / len(OBJECTIVES), rel=0.01)
    assert solution.status == SolutionStatus.FEASIBLE
    assert [stage.status for stage in solution.stages[1:]] == [SolutionStatus.FEASIBLE] * (len(OBJECTIVES) - 1)
    assert checked(solution).status == CheckStatus.ACCEPTED
    assert stages_are_scores(solution)


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


def gap(day: date, shift_: Shift, missing: int = 1, level: StaffLevel = StaffLevel.PROFESSIONAL, unit: int = NORTH):
    return Gap(
        planning_unit_id=unit,
        date=day,
        shift_id=shift_.shift_id,
        staff_level=level,
        missing_count=missing,
    )


def test_unmet_demand_returns_exactly_the_missing_slots_as_gaps() -> None:
    data = dataset(
        memberships=[*member(1, StaffLevel.MFA), *member(2, StaffLevel.ASSISTANT)],
        accounts=[account(1, 420), account(2, 0)],
        demand=[need(jan(5), EARLY, count=2, level=StaffLevel.MFA)],
    )
    solution = solve(data)

    assert solution.status == SolutionStatus.OPTIMAL
    assert solution.assignments == (duty(1, jan(5), EARLY, level=StaffLevel.MFA),)
    assert solution.gaps == (gap(jan(5), EARLY, level=StaffLevel.MFA),)
    assert checked(solution).status == CheckStatus.ACCEPTED
    assert stages_are_scores(solution)
    assert [(row.code, row.severity) for row in solution.diagnostics] == [
        ("staffing.too_few_candidates", DiagnosticSeverity.WARNING)
    ]


def test_a_gap_is_never_traded_for_health_events() -> None:
    # Filling both duties steps back from late to early; leaving one open would avoid that.
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 435 + 420)],
        demand=[need(jan(10), LATE), need(jan(12), EARLY)],
    )
    solution = solve(data)

    assert solution.gaps == ()
    assert checked(solution).scores.backward_transitions == 1
    assert stages_are_scores(solution)


def test_a_non_staffing_conflict_stays_infeasible() -> None:
    # Gaps relax only staffing: the jumper pool employee still has to reach the account.
    data = dataset(
        memberships=member(1, home=JUMPER_POOL),
        accounts=[account(1, 1000)],
        demand=[need(jan(5), EARLY)],
    )
    solution = solve(data)

    assert solution.status == SolutionStatus.INFEASIBLE
    assert (solution.assignments, solution.gaps, solution.check, solution.stages) == ((), (), None, ())
    assert "balance.unreachable" in [row.code for row in solution.diagnostics]


def test_a_jumper_pool_employee_cannot_fill_both_stations_on_one_date() -> None:
    data = dataset(
        memberships=member(1, StaffLevel.ASSISTANT, home=JUMPER_POOL, replacements=[NORTH, SOUTH]),
        accounts=[account(1, 420)],
        demand=[need(jan(5), EARLY, level=StaffLevel.ASSISTANT, unit=unit) for unit in (NORTH, SOUTH)],
    )
    solution = solve(data)

    assert len(solution.assignments) == len(solution.gaps) == 1
    assert checked(solution).status == CheckStatus.ACCEPTED


def wish(day: int, kind: WishType, shift_: Shift | None = None, employee_id: int = 1) -> Wish:
    return Wish(employee_id=employee_id, date=jan(day), type=kind, shift_id=shift_.shift_id if shift_ else None)


def test_fairness_spreads_unavoidable_denials_even_against_the_balance() -> None:
    # Both want January 5 and 6 off, and each day needs one of them. Employee 1's account alone would
    # take both duties; the cubic cost spreads the denials 1 + 1 instead of 2 + 0, although employee 2's
    # zero target is then exceeded by a duty.
    data = dataset(
        memberships=[*member(1), *member(2)],
        accounts=[account(1, 840), account(2, 0)],
        demand=[need(jan(5), EARLY), need(jan(6), EARLY)],
        wishes=[wish(day, WishType.FREE_DAY, employee_id=employee) for employee in (1, 2) for day in (5, 6)],
    )
    solution = solve(data)

    assert {row.employee_id for row in solution.assignments} == {1, 2}
    assert checked(solution).scores.wish_cost == 2
    assert checked(solution).scores.balance_deviation_minutes == 420
    assert stages_are_scores(solution)


def test_health_events_outweigh_a_wish() -> None:
    # A preferred early on January 12 would step back from the required late of January 10.
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 435)],
        demand=[need(jan(10), LATE)],
        wishes=[wish(12, WishType.PREFERRED_SHIFT, EARLY)],
    )
    solution = solve(data)

    assert [row.status for row in checked(solution).wishes] == [WishStatus.DENIED]
    assert checked(solution).scores.backward_transitions == 0
    assert stages_are_scores(solution)


def test_a_jumper_pool_wish_is_granted_at_a_station_and_an_ungrantable_one_costs_nothing() -> None:
    # Without wishes the zero target keeps the jumper pool employee free; the wished late is worked at
    # South, the only station they may work at. The vacation day's wish cannot be granted.
    data = dataset(
        memberships=member(1, home=JUMPER_POOL, replacements=[SOUTH]),
        accounts=[account(1, 0)],
        availability=[away(1, jan(6))],
        wishes=[wish(5, WishType.PREFERRED_SHIFT, LATE), wish(6, WishType.PREFERRED_DAY)],
    )
    solution = solve(data)

    assert solution.assignments == (duty(1, jan(5), LATE, unit=SOUTH),)
    assert [row.status for row in checked(solution).wishes] == [WishStatus.GRANTED, WishStatus.NOT_GRANTABLE]
    assert checked(solution).scores.wish_cost == 0
    assert stages_are_scores(solution)


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

    assert solution.gaps == (gap(date(2026, 10, 24), NIGHT),)
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
    assert stages_are_scores(solution)


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
    assert stages_are_scores(solution)
