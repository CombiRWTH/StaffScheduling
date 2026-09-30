--8<--
user-view/list-of-conditions.md:free-days-near-weekend
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/objectives/free_days_near_weekend.py"
# Reward free Fridays, Saturdays, Sundays, and Mondays by penalizing shifts on those days
return (
    Penalty(
        objective_id=self.id,
        name="shifts_near_weekend_penalty",
        expression=shifts_near_weekend_expr,
        multiplier=1,
    ),
)
```

This objective penalizes assigning shifts on Fridays, Mondays, or weekend days when an adjacent day is already free, encouraging contiguous long weekends for ward staff.
