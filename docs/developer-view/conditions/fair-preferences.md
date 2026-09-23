--8<--
user-view/list-of-conditions.md:fair-preferences
--8<--

### Implemented using Google's OR-Tools

Wish fulfillment is handled by `FairPreferencesObjective`:

```python title="src/scheduling/solver/cp_sat/objectives/fair_preferences.py"
class FairPreferencesObjective:
    """Penalize repeated wish violations increasingly per employee.

    Day-level wishes count as three strikes.
    Shift-specific wishes count as one strike.

    Violations are grouped by employee and wish category. Repeated violations
    become increasingly expensive through cubic penalty tiers.
    """

    id: ClassVar[str] = "fair_preferences"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        ...
        free_wish_violations = self._free_wish_violations(...)
        preferred_wish_violations = self._preferred_wish_violations(...)

        free_wish_penalties = self._bucketed_penalties(ctx, free_wish_violations, wish_group="free")
        preferred_wish_penalties = self._bucketed_penalties(ctx, preferred_wish_violations, wish_group="preferred")

        return free_wish_penalties + preferred_wish_penalties
```

Violations of "free" wishes (someone worked when they asked not to) and
"preferred" wishes (someone didn't work when they asked to) are counted
separately per employee, so one doesn't offset the other. Below is the
reasoning behind how the penalties are actually computed, since this
objective is newer.

## How the penalty is built

Every assignment decision in the model is a binary variable
$x_{e,d,s,\ell}$ meaning "employee $e$ works shift $s$ on day $d$ at level
$\ell$" (this is `ctx.assignment_variables`). To check whether someone
worked at all on a given day, or worked one particular shift, we take the
OR over the relevant variables:

$$
w_{e,d} = \bigvee_{s,\ell} x_{e,d,s,\ell}, \qquad
w_{e,d,s} = \bigvee_{\ell} x_{e,d,s,\ell}.
$$

Since these are binary variables, OR is just a max, and that's what `_worked_variable` builds in the code.

Each employee wish then gets translated into a violation flag $v_w$ and a
weight $\gamma_w$ depending on its type. A `FREE_DAY` wish is violated when
$v_w = w_{e_w,d_w}$, i.e. the employee worked at all that day, and it counts
for $\gamma_w=3$. A `FREE_SHIFT` wish is violated when $v_w = w_{e_w,d_w,s_w}$
— the employee worked that specific unwanted shift — and only counts for
$\gamma_w=1$. The two `PREFERRED_*` types work the other way round:
`PREFERRED_DAY` is violated when $v_w = 1-w_{e_w,d_w}$ (the employee didn't
work at all that day, weight 3), and `PREFERRED_SHIFT` when
$v_w = 1-w_{e_w,d_w,s_w}$ (the employee didn't work the wanted shift, weight
1).

Day-level wishes weigh three times as much as single-shift wishes. For the
`PREFERRED_*` cases the code actually builds the opposite indicator first —
"fulfilled" — and then flips it with $v_w + f_w = 1$. Wishes that point at a
day/shift with no matching assignment variables just get skipped, they
can't contribute either way.

## Why the penalty grows the way it does

For one employee and one wish group (`free` or `preferred`), add up all the
weighted violations:

$$
S = \sum_{e_w=e,\ g_w=g} \gamma_w v_w ,
$$

bounded between 0 and $\overline{S}$, the sum of all applicable weights (in
the code these are `total_strikes` and `maximum_strikes`). The idea is that
the $k$-th strike should cost $k^3$, so the second violation costs more
than the first, the third costs even more than that, and so on. The problem
is that $S$ is itself a variable, so you can't just write "$S^3$" as a
constraint. What the code does instead is split $S$ into a row of booleans,
one per possible strike level, and only let them switch on in order:

```python title="src/scheduling/solver/cp_sat/objectives/fair_preferences.py"
tier_variables = [
    ctx.model.new_bool_var(f"fair_preferences__{wish_group}__employee_{employee_id}__tier_{tier}")
    for tier in range(1, maximum_strikes + 1)
]
ctx.model.add(sum(tier_variables) == total_strikes)
for lower_tier, higher_tier in zip(tier_variables, tier_variables[1:], strict=False):
    ctx.model.add(lower_tier >= higher_tier)
tier_cost_expressions = [
    tier**3 * tier_variable for tier, tier_variable in enumerate(tier_variables, start=1)
]
```

So we get booleans $\tau_1,\dots,\tau_{\overline S}$ with
$\sum_k \tau_k = S$ and $\tau_k \ge \tau_{k+1}$. Because they're forced to
be non-increasing, they can only ever look like a block of 1's followed by
0's. And since the block of 1's has to sum to $S$, the first exactly $S$ tiers are on and the rest are off. 
That means the total cost ends up being

$$
C = \sum_{k=1}^{S} k^3 = \left(\frac{S(S+1)}{2}\right)^{2}
$$

(the sum of the first $S$ cubes happens to equal the square of the $S$-th
triangular number). So each individual strike does cost cubically more than
the one before it, matching what the docstring says, but because we're
summing all of them up, the total penalty actually grows with the fourth
power of $S$. Practically: if an employee already has a couple of
violations and picks up two more, the added penalty is much steeper than it
would be for someone starting from zero — which is the whole point, it
pushes the solver toward spreading denials around instead of dumping them
all on one person.

## The two helper functions

```python
@staticmethod
def _worked_variable(ctx, assignment_variables, *, name):
    worked = ctx.model.new_bool_var(name)
    ctx.model.add_max_equality(worked, list(assignment_variables))
    return worked
```

This creates a new boolean and ties it to the max of the given
variables, i.e. $w = \max(x_1,\dots,x_n)$, which for binaries is the usual
OR trick $w\ge x_i$ for all $i$, $w\le\sum_i x_i$. It gets used twice: once
directly as the violation flag for `FREE_*` wishes, and once as the
"fulfilled" flag for `PREFERRED_*` wishes, which then gets negated.

```python
@staticmethod
def _sum_linear_expressions(expressions):
    if not expressions:
        raise ValueError("At least one linear expression is required.")
    total = expressions[0]
    for expression in expressions[1:]:
        total += expression
    return total
```

This adds up a list of OR-Tools `LinearExpr` objects by hand instead of using Python's `sum()`, because `sum()` starts from the integer `0` by default and that doesn't always function with `LinearExpr`.

