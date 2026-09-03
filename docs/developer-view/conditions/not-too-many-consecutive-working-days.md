--8<--
user-view/list-of-conditions.md:min-working-phases
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/objectives/not_too_many_consecutive_days.py"
# Penalize consecutive working day streaks exceeding allowed length (e.g. 5 or 6+ days)
return (
    Penalty(
        objective_id=self.id,
        name="excessive_consecutive_working_days",
        expression=sum(excess_streak_vars),
    ),
)
```

For each employee, the solver identifies consecutive working day streaks longer than the maximum recommended threshold (typically 5 consecutive days) and penalizes every additional day worked without an intervening day off.
