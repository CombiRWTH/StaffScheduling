"""The objective of a month: prioritized tiers with derived dominance weights.

Each tier is named after its `ObjectiveWeights` and `ScheduleScores` field and sums one or more
terms. A term is an exact model expression of what the schedule check scores, with the largest
value it can take. The weights make one unit of a higher tier outweigh any possible change of all
lower tiers together, so the solver's objective value equals the check's weighted total.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from app.domain import POLICY, SHIFT_ORDER, WORKED_DAYS_WINDOW, ShiftType, dates_between
from app.solver.model.candidates import CandidateModel, Expr, by_day
from app.solver.models import ObjectiveWeights

# CP-SAT reports objective values as floats; staying below 2**53 keeps every weighted total exact.
MAX_OBJECTIVE = 2**53


@dataclass(frozen=True, slots=True)
class Term:
    expr: Expr
    # The largest value `expr` can take.
    bound: int


@dataclass(frozen=True, slots=True)
class Tier:
    name: str
    terms: tuple[Callable[[CandidateModel], Term], ...]
    # A reward is maximized instead of minimized.
    reward: bool = False


def six_day_windows(model: CandidateModel) -> Term:
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
    return Term(sum(events, 0), len(events))


def backward_transitions(model: CandidateModel) -> Term:
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
    return Term(sum(events, 0), len(events))


def balance_deviation(model: CandidateModel) -> Term:
    """The sum of every employee's absolute monthly balance in minutes, bounded by the hard balance band."""
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
    return Term(sum(deviations, 0), tolerance * len(deviations))


def surplus_intermediate(model: CandidateModel) -> Term:
    """Intermediate duties beyond the required ones; at most one per employee-day with such a candidate."""
    intermediate = {s.shift_id for s in model.dataset.shifts if s.type == ShiftType.INTERMEDIATE}
    duties = [duty for duty in model.candidates if duty.shift_id in intermediate]
    required = sum(row.required_count for row in model.dataset.demand_requirements if row.shift_id in intermediate)
    employee_days = {(duty.employee_id, duty.date) for duty in duties}
    return Term(sum((model.candidates[duty] for duty in duties), 0) - required, len(employee_days))


# The objective tiers, highest priority first.
OBJECTIVES: tuple[Tier, ...] = (
    Tier("health_events", (six_day_windows, backward_transitions)),
    Tier("balance_deviation_minutes", (balance_deviation,)),
    Tier("surplus_intermediate_duties", (surplus_intermediate,), reward=True),
)


def set_objective(model: CandidateModel) -> ObjectiveWeights:
    """Minimize the weighted tiers and return their weights; raises ValueError if they could exceed exact integers."""
    weighted: list[Expr] = []
    weights: dict[str, int] = {}
    # The largest weighted total of all lower tiers.
    lower = 0
    for tier in reversed(OBJECTIVES):
        terms = [term(model) for term in tier.terms]
        weights[tier.name] = lower + 1
        lower += weights[tier.name] * sum(term.bound for term in terms)
        sign = -1 if tier.reward else 1
        weighted.append(sign * weights[tier.name] * sum((term.expr for term in terms), 0))
    if lower >= MAX_OBJECTIVE:
        raise ValueError("The month is too large for exact objective weights.")
    model.cp.minimize(sum(weighted, 0))
    return ObjectiveWeights(**weights)
