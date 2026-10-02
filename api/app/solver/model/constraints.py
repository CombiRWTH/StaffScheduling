"""The hard rules of a month as CP-SAT constraints, one function per rule; staffing is relaxed by gaps.

Each rule constrains the candidates of a `CandidateModel` and may add diagnostics. Approved
availability and the work and break pattern of a single duty decide which candidates exist, so they
are not constraints here. `domain/acceptance.py` checks every rule again, independently.
"""

from collections import defaultdict
from collections.abc import Callable
from datetime import date as Date
from datetime import timedelta

from ortools.sat.python import cp_model

from app.domain import POLICY, ShiftType, dates_between, is_working_day
from app.domain.demand import DemandKey
from app.solver.diagnostics import DiagnosticSeverity
from app.solver.model.candidates import CandidateModel, Expr, Slot, by_day, is_constant

type Constraint = Callable[[CandidateModel], None]


def one_duty_per_day(model: CandidateModel) -> None:
    """At most one duty per employee and start date, across all stations and qualifications."""
    for slots in model.timelines.values():
        for day_slots in by_day(slots).values():
            model.cp.add_at_most_one(variable for slot in day_slots for variable in slot.variables)


def rest(model: CandidateModel) -> None:
    """No two duties closer than the minimum rest from one's end to the next one's start."""
    reach = timedelta(minutes=POLICY.min_rest_minutes)
    for slots in model.timelines.values():
        for index, earlier in enumerate(slots):
            for later in slots[index + 1 :]:
                if later.times.start >= earlier.times.end + reach:
                    break
                model.at_most((earlier, later), 1)


def consecutive_nights(model: CandidateModel) -> None:
    """At most the policy's night duties on consecutive dates, including context."""
    days = dates_between(model.context.covered_from, model.context.covered_until)
    limit = POLICY.max_consecutive_nights
    for slots in model.timelines.values():
        nights = _nights(slots)
        for start in range(len(days) - limit):
            window = days[start : start + limit + 1]
            if any(day in model.month for day in window):
                model.at_most([slot for day in window for slot in nights[day]], limit)


def night_recovery(model: CandidateModel) -> None:
    """No duty starts within the recovery time after the end of a block's final night."""
    recovery = timedelta(minutes=POLICY.night_recovery_minutes)
    for slots in model.timelines.values():
        nights = _nights(slots)
        for day, night_slots in list(nights.items()):
            following = nights[day + timedelta(days=1)]
            for night in night_slots:
                for later in slots:
                    if night.times.end <= later.times.start < night.times.end + recovery and later not in following:
                        # A night on the following date makes this one not the final night.
                        model.at_most((night, later), 1, unless=following)


def work_average(model: CandidateModel) -> None:
    """The month's work stays at most the average daily work per Werktag."""
    working_days = sum(is_working_day(day) for day in model.month.dates)
    for slots in model.timelines.values():
        work = [slot.times.work_minutes * variable for slot in slots for variable in slot.variables]
        if work:
            model.cp.add(sum(work) <= POLICY.average_daily_work_minutes * working_days)


def replacement_rest(model: CandidateModel) -> None:
    """Each worked Sunday/holiday of the month gets its own free Werktag of the month inside its window."""
    for slots in model.timelines.values():
        _replacement_rest(model, slots)


def _replacement_rest(model: CandidateModel, slots: list[Slot]) -> None:
    touched: dict[Date, Expr] = {}

    def works(day: Date) -> Expr:
        if day not in touched:
            touching = [slot for slot in slots if slot.times.touches(day)]
            if any(slot.fixed for slot in touching):
                touched[day] = 1
            elif not touching:
                touched[day] = 0
            else:
                flag = model.cp.new_bool_var(f"works_{day:%Y%m%d}")
                variables = [variable for slot in touching for variable in slot.variables]
                for variable in variables:
                    model.cp.add_implication(variable, flag)
                model.cp.add(flag <= sum(variables))
                touched[day] = flag
        return touched[day]

    matches: defaultdict[Date, list[cp_model.IntVar]] = defaultdict(list)
    for day in model.month.dates:
        days = POLICY.replacement_days(day)
        if days is None or is_constant(worked := works(day), 0):
            continue
        options: list[cp_model.IntVar] = []
        for free in model.month.dates:
            if abs((free - day).days) > days or not is_working_day(free) or is_constant(busy := works(free), 1):
                continue
            option = model.cp.new_bool_var(f"replacement_{day:%Y%m%d}_{free:%Y%m%d}")
            if not is_constant(busy, 0):
                model.cp.add(option + busy <= 1)
            matches[free].append(option)
            options.append(option)
        model.cp.add(sum(options, 0) >= worked)
    for options in matches.values():
        model.cp.add_at_most_one(options)


def staffing(model: CandidateModel) -> None:
    """Every dated demand row gets its required count of candidates credited with its qualification, or a gap.

    The gap is exactly the unfilled slots, `max(0, required - credited)`, for every schedule; the
    gap objective tier minimizes it.
    """
    covering: defaultdict[DemandKey, list[cp_model.IntVar]] = defaultdict(list)
    for duty, variable in model.candidates.items():
        covering[duty.demand_key].append(variable)
    for row in model.dataset.demand_requirements:
        variables = covering[row.demand_key]
        possible = sum(variable.index not in model.ruled_out for variable in variables)
        if possible < row.required_count:
            model.diagnose(
                "staffing.too_few_candidates",
                f"Station {row.planning_unit_id} needs {row.required_count} {row.staff_level.value} on "
                f"{row.date} (shift {row.shift_id}), but only {possible} can work it.",
                DiagnosticSeverity.WARNING,
            )
        name = f"gap_{row.planning_unit_id}_{row.date:%Y%m%d}_{row.shift_id}_{row.staff_level}"
        gap = model.cp.new_int_var(0, row.required_count, name)
        model.cp.add_max_equality(gap, [0, row.required_count - sum(variables, 0)])
        model.gaps[row] = gap


def monthly_balance(model: CandidateModel) -> None:
    """Every employee's monthly balance stays inside the tolerance band, also without any possible duty."""
    tolerance = POLICY.balance_tolerance_minutes
    for account in model.dataset.monthly_work_accounts:
        balance = model.balance(account)
        if not isinstance(balance, int):
            model.cp.add_linear_constraint(balance, -tolerance, tolerance)
        elif abs(balance) > tolerance:
            model.diagnose(
                "balance.unreachable",
                f"Employee {account.employee_id} has no possible duty, but target minus credits is "
                f"{-balance} minutes, beyond ±{tolerance}.",
            )
            # An empty clause: the month has no solution.
            model.cp.add_bool_or([])


# Every hard rule of the model. Staffing and the balance band come last: their diagnostics and
# balances skip the candidates that the context duties rule out in the rules before them.
HARD_RULES: tuple[Constraint, ...] = (
    one_duty_per_day,
    rest,
    consecutive_nights,
    night_recovery,
    work_average,
    replacement_rest,
    staffing,
    monthly_balance,
)


def _nights(slots: list[Slot]) -> defaultdict[Date, list[Slot]]:
    return by_day(slot for slot in slots if slot.shift.type == ShiftType.NIGHT)
