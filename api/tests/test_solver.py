"""Production solves of small months: every hard rule is modelled, the objective stages keep their order."""

from datetime import date
from typing import Any

import pytest
from ortools.sat.python import cp_model
from scheduling import (
    BACK_TO_BACK_WEEKENDS,
    EARLY,
    INTERMEDIATE,
    ISOLATED_WORKDAYS,
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
from app.solver.model.candidates import CandidateModel
from app.solver.model.objectives import OBJECTIVES, Term, back_to_back_weekends, isolated_workdays
from app.solver.models import Solution, SolutionStatus
from app.solver.service import SolverService

pytestmark = pytest.mark.integration

SOLVER = SolverService(Settings(solver_num_search_workers=1, solver_random_seed=1))


def solve(data: SchedulingDataset) -> Solution:
    """A production solve whose every stage, when a schedule is found, reports the checked score of its tier."""
    solution = SOLVER.solve(data, timeout=20)
    assert solution.check is None or stages_are_scores(solution)
    return solution


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
    assert all(stage.status == SolutionStatus.OPTIMAL for stage in solution.stages)
    assert all(stage.best_bound is not None and stage.value == round(stage.best_bound) for stage in solution.stages)
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

    # Each stage but the last gets half of the time left.
    assert budgets[0] == pytest.approx(30 / 2, rel=0.01)
    assert solution.status == SolutionStatus.FEASIBLE
    assert [(stage.status, stage.best_bound) for stage in solution.stages[1:]] == [(SolutionStatus.FEASIBLE, None)] * (
        len(OBJECTIVES) - 1
    )
    assert checked(solution).status == CheckStatus.ACCEPTED
    assert stages_are_scores(solution)


def term_value(term: Term, data: SchedulingDataset, schedule: tuple[Assignment, ...]) -> int:
    """The term's value with every candidate fixed to the schedule and no objective pushing it."""
    model = CandidateModel(data)
    expr = term(model)
    for duty_, variable in model.candidates.items():
        model.cp.add(variable == int(duty_ in schedule))
    solver = cp_model.CpSolver()
    assert solver.solve(model.cp) == cp_model.OPTIMAL
    return int(solver.value(expr))


@pytest.mark.parametrize(("data", "schedule", "_events"), ISOLATED_WORKDAYS)
def test_the_isolated_workdays_term_is_the_checked_score(
    data: SchedulingDataset, schedule: tuple[Assignment, ...], _events: int
) -> None:
    assert term_value(isolated_workdays, data, schedule) == check_schedule(data, schedule).scores.isolated_workdays


@pytest.mark.parametrize(("data", "schedule", "_events"), BACK_TO_BACK_WEEKENDS)
def test_the_back_to_back_weekends_term_is_the_checked_score(
    data: SchedulingDataset, schedule: tuple[Assignment, ...], _events: int
) -> None:
    assert term_value(back_to_back_weekends, data, schedule) == (
        check_schedule(data, schedule).scores.back_to_back_weekends
    )


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
        availability=only(1, {5: (EARLY.shift_id,)}),
    )
    solution = solve(data)

    assert solution.status == SolutionStatus.OPTIMAL
    assert solution.assignments == (duty(1, jan(5), EARLY, level=StaffLevel.MFA),)
    assert solution.gaps == (gap(jan(5), EARLY, level=StaffLevel.MFA),)
    assert checked(solution).status == CheckStatus.ACCEPTED
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
        availability=only(1, {5: (EARLY.shift_id,)}),
    )
    solution = solve(data)

    assert len(solution.assignments) == len(solution.gaps) == 1
    assert checked(solution).status == CheckStatus.ACCEPTED


def wish(day: int, kind: WishType, shift_: Shift | None = None, employee_id: int = 1) -> Wish:
    return Wish(employee_id=employee_id, date=jan(day), type=kind, shift_id=shift_.shift_id if shift_ else None)


def test_fairness_spreads_unavoidable_denials_even_against_the_balance() -> None:
    # Both want January 5 and 7 off, and each day needs one of them. Employee 1's account alone would
    # take both duties; the cubic cost spreads the denials 1 + 1 instead of 2 + 0, although employee 2's
    # zero target is then exceeded by a duty. Either way both duties are isolated.
    allowed = {5: (EARLY.shift_id,), 7: (EARLY.shift_id,)}
    data = dataset(
        memberships=[*member(1), *member(2)],
        accounts=[account(1, 840), account(2, 0)],
        demand=[need(jan(5), EARLY), need(jan(7), EARLY)],
        availability=[*only(1, allowed), *only(2, allowed)],
        wishes=[wish(day, WishType.FREE_DAY, employee_id=employee) for employee in (1, 2) for day in (5, 7)],
    )
    solution = solve(data)

    assert {row.employee_id for row in solution.assignments} == {1, 2}
    assert checked(solution).scores.wish_cost == 2
    # Employee 1 is a duty short and employee 2 a duty over; 2 + 0 would leave both balanced.
    assert checked(solution).scores.balance_deviation_minutes == 2 * 420


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


def test_one_isolated_workday_fewer_outweighs_a_wish() -> None:
    # The required early of January 13 needs a second duty for the balance. The preferred January 20 would
    # be isolated, the early of January 14 is not.
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 2 * 420)],
        demand=[need(jan(13), EARLY)],
        availability=only(1, {13: (EARLY.shift_id,), 14: (EARLY.shift_id,), 20: (EARLY.shift_id,)}),
        wishes=[wish(20, WishType.PREFERRED_DAY)],
    )
    solution = solve(data)

    assert solution.assignments == (duty(1, jan(13), EARLY), duty(1, jan(14), EARLY))
    assert checked(solution).scores.isolated_workdays == 0
    assert [row.status for row in checked(solution).wishes] == [WishStatus.DENIED]


def test_one_back_to_back_weekend_fewer_outweighs_a_wish() -> None:
    # The required weekend of January 10 and 11 needs a second two-day block for the balance. The preferred
    # Saturday of January 17 would make the next weekend worked too; January 14 and 15 would not.
    blocks = (10, 11, 14, 15, 17, 18)
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 4 * 420)],
        demand=[need(jan(10), EARLY), need(jan(11), EARLY)],
        availability=only(1, dict.fromkeys(blocks, (EARLY.shift_id,))),
        wishes=[wish(17, WishType.PREFERRED_DAY)],
    )
    solution = solve(data)

    assert solution.assignments == tuple(duty(1, jan(day), EARLY) for day in (10, 11, 14, 15))
    assert checked(solution).scores.back_to_back_weekends == 0
    assert [row.status for row in checked(solution).wishes] == [WishStatus.DENIED]


def test_a_jumper_pool_wish_is_granted_at_a_station_and_an_ungrantable_one_costs_nothing() -> None:
    # Without wishes the zero target keeps the jumper pool employee free; the wished late is worked at
    # South, the only station they may work at, and the trusted early of December 31 keeps it from being
    # isolated. The vacation day's wish cannot be granted.
    data = dataset(
        memberships=member(1, home=JUMPER_POOL, replacements=[SOUTH]),
        accounts=[account(1, 0)],
        availability=[away(1, jan(6))],
        wishes=[wish(1, WishType.PREFERRED_SHIFT, LATE), wish(6, WishType.PREFERRED_DAY)],
        context_duties=[duty(1, date(2025, 12, 31), EARLY, unit=SOUTH)],
    )
    solution = solve(data)

    assert solution.assignments == (duty(1, jan(1), LATE, unit=SOUTH),)
    assert [row.status for row in checked(solution).wishes] == [WishStatus.GRANTED, WishStatus.NOT_GRANTABLE]
    assert checked(solution).scores.wish_cost == 0


def test_health_events_outweigh_a_station_transfer() -> None:
    # South's early of January 12 would step its own employee 2 back from the late of January 10; North's
    # employee 1 may work at South through a replacement membership. The balance alone prefers employee 2.
    data = dataset(
        memberships=[*member(1, replacements=[SOUTH]), *member(2, home=SOUTH)],
        accounts=[account(1, 0), account(2, 435 + 420)],
        demand=[need(jan(10), LATE, unit=SOUTH), need(jan(12), EARLY, unit=SOUTH)],
        availability=[*only(1, {12: (EARLY.shift_id,)}), *only(2, {10: (LATE.shift_id,), 12: (EARLY.shift_id,)})],
    )
    solution = solve(data)

    assert duty(1, jan(12), EARLY, unit=SOUTH) in solution.assignments
    assert (checked(solution).scores.backward_transitions, checked(solution).scores.station_transfers) == (0, 1)


def test_a_station_transfer_is_never_made_to_grant_a_wish() -> None:
    # South's own employee 2 wants January 5 off; North's employee 1 could take the early by a transfer, which
    # the wish and the balance would both prefer.
    data = dataset(
        memberships=[*member(1, replacements=[SOUTH]), *member(2, home=SOUTH)],
        accounts=[account(1, 420), account(2, 0)],
        demand=[need(jan(5), EARLY, unit=SOUTH)],
        availability=only(1, {5: (EARLY.shift_id,)}),
        wishes=[wish(5, WishType.FREE_DAY, employee_id=2)],
    )
    solution = solve(data)

    assert duty(2, jan(5), EARLY, unit=SOUTH) in solution.assignments
    assert checked(solution).scores.station_transfers == 0
    assert [row.status for row in checked(solution).wishes] == [WishStatus.DENIED]


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


def test_an_intermediate_gap_never_offsets_a_surplus() -> None:
    # One employee cannot fill both intermediate slots of January 5; their intermediate duty of January 6,
    # which no row requires, is still a surplus.
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 2 * 345)],
        demand=[need(jan(5), INTERMEDIATE, count=2)],
        availability=only(1, {5: (INTERMEDIATE.shift_id,), 6: (INTERMEDIATE.shift_id,)}),
    )
    solution = solve(data)

    assert solution.gaps == (gap(jan(5), INTERMEDIATE),)
    assert checked(solution).scores.surplus_intermediate_duties == 1


@pytest.mark.parametrize(("short_by", "intermediate"), [(172, False), (173, True)])
def test_the_balance_outweighs_extra_intermediate_duties(short_by: int, intermediate: bool) -> None:
    # An optional 345-minute intermediate duty helps only if it brings the balance closer, by even one minute.
    # It follows the required block of January 9 and 10, so no day is isolated either way.
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 2 * 420 + short_by)],
        demand=[need(jan(9), EARLY), need(jan(10), EARLY)],
        availability=only(1, {9: (EARLY.shift_id,), 10: (EARLY.shift_id,), 11: (INTERMEDIATE.shift_id,)}),
    )
    solution = solve(data)
    extra: Assignment = duty(1, jan(11), INTERMEDIATE)

    assert (extra in solution.assignments) == intermediate
    assert checked(solution).scores.surplus_intermediate_duties == int(intermediate)
