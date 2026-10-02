"""The independent schedule check on the discriminating examples of the selected rule policy."""

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
    hm,
    jan,
    member,
    need,
    shift,
)

from app.domain import (
    Assignment,
    AvailabilityType,
    CheckStatus,
    Gap,
    MonthlyWorkAccount,
    PlanningMonth,
    Rule,
    SchedulingDataset,
    Shift,
    ShiftType,
    StaffLevel,
    Wish,
    WishStatus,
    WishType,
    check_schedule,
    duty_times,
)
from app.domain.duty import local_instant
from app.solver.model import build_model


def rules(data: SchedulingDataset, assignments: list[Assignment]) -> set[Rule]:
    return {finding.rule for finding in check_schedule(data, assignments).findings}


def balanced(employee_id: int, assignments: list[Assignment]) -> list[MonthlyWorkAccount]:
    """An account whose target equals the assignments' paid minutes."""
    paid = {EARLY.shift_id: 420, INTERMEDIATE.shift_id: 345, LATE.shift_id: 435, NIGHT.shift_id: 555}
    return [account(employee_id, sum(paid[row.shift_id] for row in assignments if row.employee_id == employee_id))]


def test_valid_month_is_accepted_with_its_open_obligations_listed() -> None:
    schedule = [duty(1, jan(5), EARLY), duty(1, jan(6), LATE)]
    check = check_schedule(
        dataset(memberships=member(1), accounts=balanced(1, schedule), demand=[need(jan(5), EARLY)]), schedule
    )

    assert check.status == CheckStatus.ACCEPTED
    assert check.findings == ()
    # Later obligations are named with their window and do not block; nothing is presented as passed.
    assert {(row.rule, row.blocking) for row in check.not_assessed} == {
        (Rule.REST, False),
        (Rule.ANNUAL_FREE_SUNDAYS, False),
    }
    assert Rule.ANNUAL_FREE_SUNDAYS not in check.rules


def test_missing_preceding_context_leaves_the_month_incomplete() -> None:
    schedule = [duty(1, jan(5), EARLY)]
    check = check_schedule(
        dataset(memberships=member(1), accounts=balanced(1, schedule), covered_days_before=2), schedule
    )

    assert check.status == CheckStatus.INCOMPLETE
    [gap] = [row for row in check.not_assessed if row.blocking]
    assert (gap.rule, gap.start, gap.end) == (Rule.REST, date(2025, 12, 27), date(2025, 12, 31))


def test_malformed_assignments_are_rejected_and_ignored_otherwise() -> None:
    data = dataset(memberships=member(1, home=JUMPER_POOL, replacements=[NORTH]), accounts=[account(1, 0)])
    unknown_shift = duty(1, jan(5), EARLY).model_copy(update={"shift_id": 9999})
    check = check_schedule(
        data,
        [
            unknown_shift,
            duty(1, date(2026, 2, 1), EARLY),
            duty(1, jan(6), EARLY, unit=JUMPER_POOL),
            *[duty(1, jan(7), EARLY)] * 2,
        ],
    )

    assert check.status == CheckStatus.REJECTED
    assert [row.rule for row in check.findings].count(Rule.INPUT) == 4
    # The remaining valid early is checked normally: 420 minutes over a zero target stay in the band.
    assert {row.rule for row in check.findings} == {Rule.INPUT}


def test_staffing_counts_the_qualification_each_duty_is_credited_as() -> None:
    data = dataset(
        memberships=[*member(1, StaffLevel.ASSISTANT), *member(2, StaffLevel.MFA), *member(3, StaffLevel.ASSISTANT)],
        accounts=[account(1, 420), account(2, 0), account(3, 420)],
        demand=[need(jan(10), EARLY, level=StaffLevel.MFA)],
        levels={3: StaffLevel.PROFESSIONAL},
    )

    # An assistant cannot fill the MFA minimum.
    assert rules(data, [duty(1, jan(10), EARLY, level=StaffLevel.ASSISTANT)]) == {Rule.STAFFING}
    # Credited as MFA without an MFA membership is ineligible, even though it would cover demand.
    assert Rule.ELIGIBILITY in rules(data, [duty(1, jan(10), EARLY, level=StaffLevel.MFA)])
    # The membership decides, not the employee-level qualification of employee 3.
    assert Rule.ELIGIBILITY in rules(data, [duty(3, jan(11), EARLY, level=StaffLevel.PROFESSIONAL)])
    assert (
        rules(
            data, [duty(3, jan(11), EARLY, level=StaffLevel.ASSISTANT), duty(2, jan(10), EARLY, level=StaffLevel.MFA)]
        )
        == set()
    )


def test_a_shortfall_is_accepted_only_as_exactly_its_declared_gap() -> None:
    data = dataset(memberships=member(1), accounts=[account(1, 420)], demand=[need(jan(10), EARLY, count=2)])
    schedule = [duty(1, jan(10), EARLY)]

    def gap(missing: int, day: int = 10) -> Gap:
        return Gap(
            planning_unit_id=NORTH,
            date=jan(day),
            shift_id=EARLY.shift_id,
            staff_level=StaffLevel.PROFESSIONAL,
            missing_count=missing,
        )

    accepted = check_schedule(data, schedule, [gap(1)])
    assert accepted.status == CheckStatus.ACCEPTED
    assert accepted.scores.gaps == 1
    # An undeclared shortfall, a wrong count and a gap without demand are all staffing violations.
    for declared in ([], [gap(2)], [gap(1), gap(1, day=11)]):
        check = check_schedule(data, schedule, declared)
        assert {finding.rule for finding in check.findings} == {Rule.STAFFING}
        assert check.scores.gaps == 1
    # A declared gap the assignments fill is no gap.
    filled = [*schedule, duty(2, jan(10), EARLY)]
    two = dataset(
        memberships=[*member(1), *member(2)],
        accounts=[account(1, 420), account(2, 420)],
        demand=[need(jan(10), EARLY, count=2)],
    )
    assert rules(two, filled) == set()
    assert {finding.rule for finding in check_schedule(two, filled, [gap(1)]).findings} == {Rule.STAFFING}


def wish(day: int, kind: WishType, shift_: Shift | None = None, employee_id: int = 1) -> Wish:
    return Wish(employee_id=employee_id, date=jan(day), type=kind, shift_id=shift_.shift_id if shift_ else None)


def outcomes(data: SchedulingDataset, assignments: list[Assignment]) -> list[WishStatus]:
    return [row.status for row in check_schedule(data, assignments).wishes]


def test_wishes_are_granted_denied_or_not_grantable_at_their_boundaries() -> None:
    free_day, free_early = wish(10, WishType.FREE_DAY), wish(10, WishType.FREE_SHIFT, EARLY)
    data = dataset(memberships=member(1), accounts=[account(1, 555)], wishes=[free_day])
    # A night from the evening before touches the free day; a late duty the day before does not.
    assert outcomes(data, [duty(1, jan(9), NIGHT)]) == [WishStatus.DENIED]
    assert outcomes(data, [duty(1, jan(9), LATE)]) == [WishStatus.GRANTED]
    shift_data = dataset(memberships=member(1), accounts=[account(1, 420)], wishes=[free_early])
    assert outcomes(shift_data, [duty(1, jan(10), EARLY)]) == [WishStatus.DENIED]
    assert outcomes(shift_data, [duty(1, jan(10), LATE)]) == [WishStatus.GRANTED]

    # A preferred shift is fulfilled at any station: here at the jumper pool employee's replacement station.
    wishes = [wish(10, WishType.PREFERRED_SHIFT, EARLY), wish(11, WishType.PREFERRED_DAY)]
    pool = dataset(
        memberships=member(1, home=JUMPER_POOL, replacements=[SOUTH]), accounts=[account(1, 420)], wishes=wishes
    )
    assert outcomes(pool, [duty(1, jan(10), EARLY, unit=SOUTH)]) == [WishStatus.GRANTED, WishStatus.DENIED]
    assert outcomes(pool, [duty(1, jan(10), LATE, unit=SOUTH)]) == [WishStatus.DENIED, WishStatus.DENIED]
    assert outcomes(pool, [duty(1, jan(11), LATE, unit=SOUTH)]) == [WishStatus.DENIED, WishStatus.GRANTED]

    # Binding availability, a missing station membership and a context night make wishes ungrantable.
    blocked = dataset(
        memberships=[*member(1), *member(2, home=JUMPER_POOL)],
        accounts=[account(1, 0), account(2, 0)],
        availability=[away(1, jan(10)), away(1, jan(11), AvailabilityType.AVAILABLE_ONLY, (LATE.shift_id,))],
        wishes=[
            wish(10, WishType.PREFERRED_DAY),
            wish(11, WishType.PREFERRED_SHIFT, EARLY),
            wish(1, WishType.FREE_DAY),
            wish(10, WishType.PREFERRED_DAY, employee_id=2),
        ],
        context_duties=[duty(1, date(2025, 12, 31), NIGHT)],
    )
    check = check_schedule(blocked, [])
    assert [row.status for row in check.wishes] == [WishStatus.NOT_GRANTABLE] * 4
    assert check.wish_counts == {WishStatus.GRANTED: 0, WishStatus.DENIED: 0, WishStatus.NOT_GRANTABLE: 4}
    assert check.scores.wish_cost == 0


def test_the_wish_cost_grows_cubically_per_employee_and_group() -> None:
    data = dataset(
        memberships=[*member(1), *member(2)],
        accounts=[account(1, 0), account(2, 0)],
        wishes=[
            wish(5, WishType.PREFERRED_DAY),
            wish(6, WishType.PREFERRED_DAY),
            wish(7, WishType.FREE_DAY),
            wish(5, WishType.PREFERRED_DAY, employee_id=2),
        ],
    )
    check = check_schedule(data, [duty(1, jan(7), EARLY)])

    # Employee 1: two preferred denials cost 1 + 8, the free denial 1 apart; employee 2's one denial 1.
    assert check.scores.wish_cost == 9 + 1 + 1
    assert check.wish_counts[WishStatus.DENIED] == 4


def test_station_transfers_count_station_members_at_other_stations_only() -> None:
    data = dataset(
        memberships=[*member(1, replacements=[SOUTH]), *member(2, home=JUMPER_POOL, replacements=[NORTH, SOUTH])],
        accounts=[account(1, 840), account(2, 420)],
    )
    schedule = [duty(1, jan(5), EARLY), duty(1, jan(6), EARLY, unit=SOUTH), duty(2, jan(5), EARLY, unit=SOUTH)]

    # Only the station member's replacement duty counts; jumper pool duties are never station transfers.
    assert check_schedule(data, schedule).scores.station_transfers == 1


def test_a_jumper_pool_employee_cannot_cover_both_stations_at_once() -> None:
    data = dataset(memberships=member(1, home=JUMPER_POOL, replacements=[NORTH, SOUTH]), accounts=[account(1, 840)])
    found = rules(data, [duty(1, jan(12), EARLY, unit=NORTH), duty(1, jan(12), EARLY, unit=SOUTH)])

    assert found == {Rule.ONE_DUTY_PER_DAY, Rule.REST}


def test_availability_blocks_touched_dates_and_nights_before_approved_free_days() -> None:
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 0)],
        availability=[
            away(1, jan(10)),
            away(1, jan(20), AvailabilityType.AVAILABLE_ONLY, (EARLY.shift_id, LATE.shift_id)),
            away(1, jan(20), AvailabilityType.AVAILABLE_ONLY, (LATE.shift_id, NIGHT.shift_id)),
        ],
        context_availability=[away(1, date(2026, 2, 1), AvailabilityType.FREE_DAY)],
    )

    def problems(*assignments: Assignment) -> set[Rule]:
        return rules(data, list(assignments)) - {Rule.MONTHLY_BALANCE}

    assert problems(duty(1, jan(10), LATE)) == {Rule.AVAILABILITY}
    # The night of January 9 runs into the vacation; so does the last night into February 1 after the month.
    assert problems(duty(1, jan(9), NIGHT)) == {Rule.AVAILABILITY}
    assert problems(duty(1, jan(31), NIGHT)) == {Rule.AVAILABILITY}
    assert problems(duty(1, jan(9), LATE), duty(1, jan(31), LATE)) == set()
    # Two allowed-shift restrictions narrow each other to the late shift.
    assert problems(duty(1, jan(20), EARLY)) == {Rule.AVAILABILITY}
    assert problems(duty(1, jan(20), NIGHT)) == {Rule.AVAILABILITY}
    assert problems(duty(1, jan(20), LATE)) == set()


@pytest.mark.parametrize(
    ("target", "credits", "assignments", "balance"),
    [
        # Target 9600 with 480 credited needs 9120 generated minutes to balance exactly.
        (9600, 480, 21, 9600 - 480 - 21 * 420),
        (900, 480, 1, 0),
        (900 + 460, 480, 1, -460),
        (900 - 461, 480, 1, 461),
        # Without any duty the credits alone must reach the band.
        (941, 480, 0, -461),
    ],
)
def test_monthly_balance_uses_generated_paid_minutes_and_verified_credits(
    target: int, credits: int, assignments: int, balance: int
) -> None:
    schedule = [duty(1, jan(day), EARLY) for day in range(1, assignments + 1)]
    check = check_schedule(dataset(memberships=member(1), accounts=[account(1, target, credits)]), schedule)

    failed = Rule.MONTHLY_BALANCE in {row.rule for row in check.findings}
    assert failed == (abs(balance) > 460)


def test_rest_is_measured_between_actual_duty_times() -> None:
    # Late ends 21:00, early starts 05:55: under eleven hours, whatever the codes.
    data = dataset(memberships=member(1), accounts=[account(1, 855)])
    assert Rule.REST in rules(data, [duty(1, jan(5), LATE), duty(1, jan(6), EARLY)])

    early_six = shift(2, "E6", ShiftType.EARLY, (hm(6), hm(10)), (hm(10, 30), hm(13)))
    until_seven = shift(3, "L19", ShiftType.LATE, (hm(13), hm(16)), (hm(16, 30), hm(19)))
    until_one_past = shift(4, "L1901", ShiftType.LATE, (hm(13, 1), hm(16)), (hm(16, 30), hm(19, 1)))
    data = dataset(memberships=member(1), accounts=[account(1, 750)], shifts=[early_six, until_seven, until_one_past])
    # 19:00 to 06:00 is exactly eleven hours and passes; one minute later fails.
    assert Rule.REST not in rules(data, [duty(1, jan(5), until_seven), duty(1, jan(6), early_six)])
    assert Rule.REST in rules(data, [duty(1, jan(5), until_one_past), duty(1, jan(6), early_six)])


def test_nights_are_limited_to_three_in_a_row_across_the_month_start() -> None:
    nights = [duty(1, jan(day), NIGHT) for day in (5, 6, 7)]
    data = dataset(memberships=member(1), accounts=[account(1, 1665)])
    assert Rule.CONSECUTIVE_NIGHTS not in rules(data, nights)
    assert Rule.CONSECUTIVE_NIGHTS in rules(
        dataset(memberships=member(1), accounts=[account(1, 2220)]), [*nights, duty(1, jan(8), NIGHT)]
    )

    # Three trusted December nights make a January 1 night the fourth.
    context = [duty(1, date(2025, 12, day), NIGHT) for day in (29, 30, 31)]
    data = dataset(memberships=member(1), accounts=[account(1, 555)], context_duties=context)
    assert Rule.CONSECUTIVE_NIGHTS in rules(data, [duty(1, jan(1), NIGHT)])


def test_recovery_after_the_final_night_is_48_elapsed_hours() -> None:
    # The last night ends on Tuesday, January 13, at 06:00.
    night = shift(5, "N6", ShiftType.NIGHT, (hm(22), hm(24)), (hm(0, 30, next_day=True), hm(6, next_day=True)))
    early_six = shift(2, "E6", ShiftType.EARLY, (hm(6), hm(10)), (hm(10, 30), hm(13)))
    night_eleven = shift(6, "N23", ShiftType.NIGHT, (hm(23), hm(24)), (hm(0, 30, next_day=True), hm(7, next_day=True)))
    data = dataset(memberships=member(1), accounts=[account(1, 1110)], shifts=[night, early_six, night_eleven])
    block = [duty(1, jan(11), night), duty(1, jan(12), night)]

    # Thursday 06:00 is exactly 48 hours later; Wednesday 23:00 is too early.
    assert Rule.NIGHT_RECOVERY not in rules(data, [*block, duty(1, jan(15), early_six)])
    assert Rule.NIGHT_RECOVERY in rules(data, [*block, duty(1, jan(14), night_eleven)])
    # A trusted December night recovers into January too.
    data = dataset(
        memberships=member(1), accounts=[account(1, 420)], context_duties=[duty(1, date(2025, 12, 31), NIGHT)]
    )
    assert Rule.NIGHT_RECOVERY in rules(data, [duty(1, jan(2), NIGHT)])


@pytest.mark.parametrize(
    ("segments", "problem"),
    [
        # Six hours need no break; six hours and one minute do.
        (((hm(7), hm(13)),), False),
        (((hm(7), hm(13, 1)),), True),
        # 9.5 hours of work need 45 minutes; 30 are not enough.
        (((hm(6), hm(11)), (hm(11, 30), hm(16, 30))), True),
        # A ten-minute gap is no break part: 30 of the required 45 minutes qualify.
        (((hm(6), hm(11)), (hm(11, 30), hm(15, 30)), (hm(15, 40), hm(16, 10))), True),
        (((hm(6), hm(11)), (hm(11, 15), hm(14)), (hm(14, 30), hm(16, 15))), False),
        # Ten-minute gaps are no break parts; 6h10 of work runs without a qualifying break.
        (((hm(6), hm(9)), (hm(9, 10), hm(12, 20))), True),
        # More than ten hours of work are never allowed.
        (((hm(6), hm(11)), (hm(11, 30), hm(15)), (hm(15, 15), hm(17, 45))), True),
    ],
)
def test_daily_work_and_breaks_follow_the_segments(segments: tuple[tuple[int, int], ...], problem: bool) -> None:
    pattern = shift(9, "X", ShiftType.OTHER, *segments)
    data = dataset(memberships=member(1), accounts=[account(1, pattern.net_work_minutes)], shifts=[pattern])
    # The check and the solver implement the rule separately and agree on every boundary.
    assert (Rule.WORK_AND_BREAKS in rules(data, [duty(1, jan(5), pattern)])) == problem
    assert ("shift.breaks_rules" in {row.code for row in build_model(data).diagnostics}) == problem


def test_monthly_work_averages_at_most_eight_hours_per_werktag() -> None:
    # 9.5 hours of work with the required 45-minute break.
    long_day = shift(7, "T", ShiftType.OTHER, (hm(7), hm(12)), (hm(12, 45), hm(17, 15)))
    february = PlanningMonth(year=2026, month=2)
    # February 2026 has 24 Werktage: at most 24 x 480 = 11520 minutes of work alongside a long duty.
    data = dataset(memberships=member(1), accounts=[account(1, 0, month=february)], shifts=[long_day], month=february)

    def check(days: int):
        return check_schedule(data, [duty(1, date(2026, 2, day), long_day) for day in range(1, days + 1)])

    assert Rule.WORK_AVERAGE not in {row.rule for row in check(20).findings}
    assert Rule.WORK_AVERAGE in {row.rule for row in check(21).findings}
    # The month is its own compensation period: nothing is left for a longer one.
    assert all(row.rule != Rule.WORK_AVERAGE for row in check(20).not_assessed)


def replacement_missing(data: SchedulingDataset, assignments: list[Assignment]) -> set[date | None]:
    return {row.date for row in check_schedule(data, assignments).findings if row.rule == Rule.REPLACEMENT_REST}


def test_each_worked_sunday_and_holiday_needs_its_own_free_werktag_of_the_month() -> None:
    every_day = [duty(1, jan(day), EARLY) for day in range(1, 32)]
    data = dataset(memberships=member(1), accounts=[account(1, 31 * 420)])
    # New Year and all four Sundays are worked and the month has no free Werktag.
    assert replacement_missing(data, every_day) == {jan(1), jan(4), jan(11), jan(18), jan(25)}
    assert all(row.rule != Rule.REPLACEMENT_REST for row in check_schedule(data, every_day).not_assessed)

    # One free Wednesday serves one of them, never two.
    free_wednesday = [row for row in every_day if row.date != jan(7)]
    data = dataset(memberships=member(1), accounts=[account(1, 30 * 420)])
    assert len(replacement_missing(data, free_wednesday)) == 4


@pytest.mark.parametrize(("saturday", "sunday_worked"), [(LATE, False), (NIGHT, True)])
def test_a_saturday_night_is_sunday_work(saturday: Shift, sunday_worked: bool) -> None:
    # Every Werktag from January 2 to 24 is worked, so Sunday January 11 has no free Werktag in its window.
    werktage = [duty(1, jan(day), EARLY) for day in range(2, 25) if day not in (4, 10, 11, 18)]
    schedule = [*werktage, duty(1, jan(10), saturday)]
    data = dataset(memberships=member(1), accounts=balanced(1, schedule))
    assert (jan(11) in replacement_missing(data, schedule)) == sunday_worked


def test_daylight_saving_changes_elapsed_work_but_not_paid_minutes() -> None:
    # The night of March 28, 2026 loses an hour at 02:00.
    times = duty_times(date(2026, 3, 28), NIGHT)
    assert (times.work_minutes, NIGHT.net_work_minutes) == (555 - 60, 555)
    with pytest.raises(ValueError, match="skipped or repeated"):
        local_instant(date(2026, 3, 29), hm(2, 30))
    with pytest.raises(ValueError, match="skipped or repeated"):
        local_instant(date(2026, 10, 25), hm(2, 30))


def test_rest_and_recovery_count_elapsed_hours_across_clock_changes() -> None:
    early_six = shift(2, "E6", ShiftType.EARLY, (hm(6), hm(10)), (hm(10, 30), hm(13)))
    until_seven = shift(3, "L19", ShiftType.LATE, (hm(13), hm(16)), (hm(16, 30), hm(19)))
    march = PlanningMonth(year=2026, month=3)
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 750, month=march)],
        shifts=[early_six, until_seven, NIGHT],
        month=march,
    )
    # 19:00 to 06:00 is eleven hours, but only ten elapse into March 29, when clocks skip an hour.
    assert Rule.REST not in rules(
        data, [duty(1, date(2026, 3, 21), until_seven), duty(1, date(2026, 3, 22), early_six)]
    )
    assert Rule.REST in rules(data, [duty(1, date(2026, 3, 28), until_seven), duty(1, date(2026, 3, 29), early_six)])

    october = PlanningMonth(year=2026, month=10)
    data = dataset(memberships=member(1), accounts=[account(1, 975, month=october)], month=october)
    # The night ends Saturday, October 24, 06:10; the repeated hour makes Monday 05:55 48 h 45 min later.
    assert Rule.NIGHT_RECOVERY not in rules(
        data, [duty(1, date(2026, 10, 23), NIGHT), duty(1, date(2026, 10, 26), EARLY)]
    )


def test_context_counts_for_sequences_but_never_for_demand_or_accounts() -> None:
    data = dataset(
        memberships=member(1),
        accounts=[account(1, 0)],
        demand=[need(jan(1), NIGHT)],
        context_duties=[duty(1, date(2025, 12, 31), NIGHT)],
    )
    check = check_schedule(data, [])
    assert {row.rule for row in check.findings} == {Rule.STAFFING}
    assert check.scores.balance_deviation_minutes == 0


@pytest.mark.parametrize(("days", "windows"), [(5, 0), (6, 1), (7, 2)])
def test_six_fully_worked_days_count_as_one_health_event(days: int, windows: int) -> None:
    schedule = [duty(1, jan(day), LATE) for day in range(5, 5 + days)]
    assert (
        check_schedule(dataset(memberships=member(1), accounts=[account(1, 0)]), schedule).scores.six_day_windows
        == windows
    )


def test_backward_transitions_skip_off_days_and_intermediate_duties() -> None:
    data = dataset(memberships=member(1), accounts=[account(1, 0)], context_duties=[duty(1, date(2025, 12, 30), NIGHT)])
    schedule = [
        # December's night followed by an early: backward, counted in January.
        duty(1, jan(3), EARLY),
        duty(1, jan(5), LATE),
        duty(1, jan(6), INTERMEDIATE),
        # Late, intermediate, early: backward; the intermediate has no position.
        duty(1, jan(8), EARLY),
        duty(1, jan(12), NIGHT),
        # Two off days do not reset the comparison: night to late is backward.
        duty(1, jan(15), LATE),
    ]
    assert check_schedule(data, schedule).scores.backward_transitions == 3


def test_surplus_counts_intermediate_duties_beyond_the_minimum() -> None:
    data = dataset(
        memberships=[*member(1), *member(2)],
        accounts=[account(1, 0), account(2, 0)],
        demand=[need(jan(5), INTERMEDIATE)],
    )
    schedule = [duty(1, jan(5), INTERMEDIATE), duty(2, jan(5), INTERMEDIATE), duty(1, jan(7), INTERMEDIATE)]
    assert check_schedule(data, schedule).scores.surplus_intermediate_duties == 2
    assert check_schedule(data, schedule).scores.health_events == 0


def test_the_month_must_start_after_its_covered_context() -> None:
    with pytest.raises(ValueError, match="coverage must include"):
        dataset(memberships=member(1), accounts=[account(1, 0)], covered_days_before=-1)
    with pytest.raises(ValueError, match="outside the planning month"):
        dataset(memberships=member(1), accounts=[account(1, 0)], context_duties=[duty(1, jan(3), EARLY)])
    with pytest.raises(ValueError, match="exactly one monthly account"):
        dataset(memberships=member(1), accounts=[])
    assert JANUARY.start == jan(1)
