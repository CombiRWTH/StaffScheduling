"""The objective of a month: prioritized tiers, solved one stage per tier in `OBJECTIVES` order.

Each tier is named after its `ScheduleScores` field and sums one or more terms. A term is a model
expression that equals what the schedule check scores for every schedule the hard rules allow, not
only an optimal one, so each stage's value is the check's score of the schedule it returns.
"""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta

from app.domain import FREE_WISHES, POLICY, SHIFT_ORDER, WORKED_DAYS_WINDOW, ShiftType, WishType, dates_between
from app.domain.planning_unit import home_unit_id
from app.solver.model.candidates import CandidateModel, Expr, Slot, by_day

type Term = Callable[[CandidateModel], Expr]


@dataclass(frozen=True, slots=True)
class Tier:
    name: str
    terms: tuple[Term, ...]
    # A reward is maximized instead of minimized.
    reward: bool = False


def gaps(model: CandidateModel) -> Expr:
    """Required slots that no candidate fills, as the staffing rule declares them."""
    return sum(model.gaps.values(), 0)


def six_day_windows(model: CandidateModel) -> Expr:
    """Fully worked six-day windows, each counted on its last day inside the month."""
    events: list[Expr] = []
    for slots in model.timelines.values():
        worked = by_day(slots)
        for day in model.month.dates:
            window = [day - timedelta(days=offset) for offset in range(WORKED_DAYS_WINDOW)]
            if not all(worked[d] for d in window):
                continue
            event = model.cp.new_bool_var(f"six_days_{day:%Y%m%d}")
            exprs = [sum((slot.expr for slot in worked[d]), 0) for d in window]
            model.cp.add(event >= sum(exprs) - (WORKED_DAYS_WINDOW - 1))
            for expr in exprs:
                model.cp.add(event <= expr)
            events.append(event)
    return sum(events, 0)


def backward_transitions(model: CandidateModel) -> Expr:
    """Successive early/late/night duties that step back in that order; off days do not reset it.

    The comparison starts with the preceding context days. `last[rank]` is 1 exactly when the most
    recent ranked duty so far had that rank.
    """
    ranks = sorted(set(SHIFT_ORDER.values()))
    events: list[Expr] = []
    for slots in model.timelines.values():
        ranked_by_day = by_day(slot for slot in slots if slot.shift.type in SHIFT_ORDER)
        last: dict[int, Expr] = dict.fromkeys(ranks, 0)
        for day in dates_between(model.month.start - timedelta(days=POLICY.preceding_context_days), model.month.end):
            ranked = {rank: [s for s in ranked_by_day[day] if SHIFT_ORDER[s.shift.type] == rank] for rank in ranks}
            if day not in model.month:
                if worked := [rank for rank in ranks if ranked[rank]]:
                    last = {rank: int(rank == worked[-1]) for rank in ranks}
                continue
            on = {rank: sum((s.expr for s in ranked[rank]), 0) for rank in ranks}
            for rank in ranks:
                for earlier_rank in ranks:
                    if earlier_rank > rank and ranked[rank]:
                        events.append(model.logical_and(on[rank], last[earlier_rank]))
            any_ranked = sum(on.values(), 0)
            last = {rank: on[rank] + model.and_not(last[rank], any_ranked) for rank in ranks}
    return sum(events, 0)


def isolated_workdays(model: CandidateModel) -> Expr:
    """Month dates with a duty starting on them but on neither neighbouring date, a single night included.

    A neighbouring date outside the month is free only inside the trusted context, so a month edge
    without context never isolates a duty.
    """
    events: list[Expr] = []
    for slots in model.timelines.values():
        starting = by_day(slots)
        for day in model.month.dates:
            if starting[day]:
                before, after = (_starts(model, starting, day + timedelta(days=step)) for step in (-1, 1))
                events.append(model.and_not(model.and_not(_starts(model, starting, day), before), after))
    return sum(events, 0)


def back_to_back_weekends(model: CandidateModel) -> Expr:
    """Pairs of consecutive worked weekends, each counted in the month of its later Sunday.

    A weekend is worked when a duty touches its Saturday or Sunday, so a Friday night counts. A pair
    counts only when the earlier weekend's Friday lies within the preceding context days.
    """
    lookback = model.month.start - timedelta(days=POLICY.preceding_context_days)
    week = timedelta(days=7)
    sundays = [day for day in model.month.dates if day.isoweekday() == 7 and day - week - timedelta(days=2) >= lookback]
    events: list[Expr] = []
    for slots in model.timelines.values():
        worked = {sunday: _worked_weekend(model, slots, sunday) for sunday in {*sundays, *(s - week for s in sundays)}}
        events.extend(model.logical_and(worked[sunday - week], worked[sunday]) for sunday in sundays)
    return sum(events, 0)


def _starts(model: CandidateModel, starting: dict[Date, list[Slot]], day: Date) -> Expr:
    """1 when a duty starts on the date, also when it lies outside the month and its trusted context."""
    if day not in model.month and not model.context.covers(day):
        return 1
    if any(slot.fixed for slot in starting[day]):
        return 1
    return sum((variable for slot in starting[day] for variable in slot.variables), 0)


def _worked_weekend(model: CandidateModel, slots: list[Slot], sunday: Date) -> Expr:
    """1 when a duty touches the Sunday or the Saturday before it."""
    touching = [slot for slot in slots if slot.times.touches(sunday - timedelta(days=1)) or slot.times.touches(sunday)]
    if any(slot.fixed for slot in touching):
        return 1
    return model.any_of([variable for slot in touching for variable in slot.variables])


def station_transfers(model: CandidateModel) -> Expr:
    """Candidates of employees whose origin that date is a station, at another station; never jumper pool duties."""
    memberships, stations = model.dataset.planning_unit_memberships, model.dataset.station_ids
    return sum(
        (
            variable
            for duty, variable in model.candidates.items()
            if (home := home_unit_id(memberships, duty.employee_id, duty.date)) in stations
            and home != duty.planning_unit_id
        ),
        0,
    )


def wish_cost(model: CandidateModel) -> Expr:
    """Denied grantable wishes, free and preferred apart per employee: the k-th denial costs k³.

    The convex cost spreads denials over employees. Its strikes are ordered booleans, so the first S
    of them are set for S denials and the cost is exact for every schedule. A wish that no candidate
    can grant (a trusted context duty touches a free day, no candidate for a preferred one) costs nothing.
    """
    denials: defaultdict[tuple[int, bool], list[Expr]] = defaultdict(list)
    for wish in model.dataset.wishes:
        slots = model.timelines[wish.employee_id]
        starting = [slot for slot in slots if slot.day == wish.date and wish.shift_id in (None, slot.shift.shift_id)]
        match wish.type:
            case WishType.FREE_DAY:
                touching = [slot for slot in slots if slot.times.touches(wish.date)]
                if any(slot.fixed for slot in touching):
                    continue
                denied = model.any_of([variable for slot in touching for variable in slot.variables])
            case WishType.FREE_SHIFT:
                denied = model.any_of([variable for slot in starting for variable in slot.variables])
            case WishType.PREFERRED_DAY | WishType.PREFERRED_SHIFT:
                if not starting:
                    continue
                denied = 1 - model.any_of([variable for slot in starting for variable in slot.variables])
        denials[(wish.employee_id, wish.type in FREE_WISHES)].append(denied)
    costs: list[Expr] = []
    for denied in denials.values():
        strikes = [model.cp.new_bool_var("strike") for _ in denied]
        model.cp.add(sum(strikes) == sum(denied, 0))
        for lower, higher in zip(strikes, strikes[1:], strict=False):
            model.cp.add(lower >= higher)
        costs.append(sum(k**3 * strike for k, strike in enumerate(strikes, start=1)))
    return sum(costs, 0)


def balance_deviation(model: CandidateModel) -> Expr:
    """The sum of every employee's absolute monthly balance in minutes."""
    tolerance = POLICY.balance_tolerance_minutes
    deviations: list[Expr] = []
    for account in model.dataset.monthly_work_accounts:
        balance = model.balance(account)
        if isinstance(balance, int):
            deviations.append(abs(balance))
            continue
        deviation = model.cp.new_int_var(0, tolerance, f"deviation_{account.employee_id}")
        model.cp.add_abs_equality(deviation, balance)
        deviations.append(deviation)
    return sum(deviations, 0)


def surplus_intermediate(model: CandidateModel) -> Expr:
    """Intermediate duties beyond the required ones, per demand row.

    Each row's surplus `max(0, credited - required)` is `credited - required + gap`, so a gap never
    offsets a surplus elsewhere; duties without a demand row count fully.
    """
    intermediate = {s.shift_id for s in model.dataset.shifts if s.type == ShiftType.INTERMEDIATE}
    duties = sum((variable for duty, variable in model.candidates.items() if duty.shift_id in intermediate), 0)
    rows = [row for row in model.dataset.demand_requirements if row.shift_id in intermediate]
    return duties - sum(row.required_count for row in rows) + sum((model.gaps[row] for row in rows), 0)


# The objective tiers, highest priority first.
OBJECTIVES: tuple[Tier, ...] = (
    Tier("gaps", (gaps,)),
    Tier("health_events", (six_day_windows, backward_transitions, isolated_workdays, back_to_back_weekends)),
    Tier("station_transfers", (station_transfers,)),
    Tier("wish_cost", (wish_cost,)),
    Tier("balance_deviation_minutes", (balance_deviation,)),
    Tier("surplus_intermediate_duties", (surplus_intermediate,), reward=True),
)


def tier_objectives(model: CandidateModel) -> tuple[tuple[Tier, Expr], ...]:
    """Every tier of `OBJECTIVES` with the sum of its terms, highest priority first."""
    return tuple((tier, sum((term(model) for term in tier.terms), 0)) for tier in OBJECTIVES)
