!!! note "Likelihood of Confusion"
    Different than the hard constraint [Free day after Night Shift Phase](./free-day-after-night-shift-phase.md).

--8<--
user-view/list-of-conditions.md:free-days-after-night-shift-phase
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/objectives/free_day_after_night_shift_phase.py"
# Penalize having only a single free day after a night shift phase (aiming for 2 full recovery days)
ctx.model.add(penalty_var == 1).only_enforce_if([night_today, next_day_free, day_after_next_worked])
ctx.model.add(penalty_var == 0).only_enforce_if(night_today.Not())

return (
    Penalty(
        objective_id=self.id,
        name="insufficient_night_recovery_days",
        expression=sum(penalties),
    ),
)
```

While the hard constraint guarantees at least 24 hours of rest after a night shift block, this soft objective rewards providing a second consecutive day off (48 hours total rest) before the employee is scheduled to work again.
