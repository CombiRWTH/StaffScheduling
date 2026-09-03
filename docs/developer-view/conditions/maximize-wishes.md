--8<--
user-view/list-of-conditions.md:maximize-wishes
--8<--

### Implemented using Google's OR-Tools

In the modern solver architecture, wish fulfillment is handled by **`FairPreferencesObjective`**, which balances wish fulfillment with equitable fairness across all employees:

```python title="src/scheduling/solver/cp_sat/objectives/fair_preferences.py"
class FairPreferencesObjective:
    """Penalize repeated wish violations increasingly per employee.

    Day-level wishes count as three strikes.
    Shift-specific wishes count as one strike.

    Violations are grouped by employee and wish category. Repeated violations
    become increasingly expensive through progressive penalty tiers.
    """

    id: ClassVar[str] = "fair_preferences"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        ...
        free_wish_violations = self._free_wish_violations(...)
        preferred_wish_violations = self._preferred_wish_violations(...)

        # Applies progressive bucketed penalty tiers so denying multiple wishes
        # to the same employee is penalized much more heavily than spreading denials
        return (
            *self._bucketed_penalties(ctx, free_wish_violations, ...),
            *self._bucketed_penalties(ctx, preferred_wish_violations, ...),
        )
```

### Progressive Penalty Tiers

To ensure fairness, denying a second or third wish to the *same* employee incurs a sharply increasing penalty compared to denying a first wish to another employee. This prevents the solver from sacrificing one person's preferences completely to satisfy everyone else.
