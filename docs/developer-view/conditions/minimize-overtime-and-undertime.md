--8<--
user-view/list-of-conditions.md:min-over-and-undertime
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/objectives/minimize_overtime.py"
# Penalize absolute deviation from monthly contracted working hours
# overtime_excess >= total_minutes - target_minutes
# undertime_deficit >= target_minutes - total_minutes
ctx.model.add(overtime_excess >= total_minutes - target_minutes)
ctx.model.add(undertime_deficit >= target_minutes - total_minutes)

return (
    Penalty(
        objective_id=self.id,
        name="total_overtime_minutes",
        expression=sum(overtime_penalties),
    ),
)
```

While contracted monthly hours are bounded within hard tolerance limits by the [Target Working Time](./target-working-time-per-month.md) constraint, this soft objective penalizes any minute of deviation, pulling total scheduled work time as close as possible to each employee's exact target.
