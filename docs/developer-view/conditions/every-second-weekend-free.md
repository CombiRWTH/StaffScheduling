--8<--
user-view/list-of-conditions.md:every-second-weekend-free
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/objectives/every_second_weekend_free.py"
# A weekend is free only if both Saturday AND Sunday are free
ctx.model.add(sat_var + sun_var == 0).only_enforce_if(weekend_free)
ctx.model.add(sat_var + sun_var >= 1).only_enforce_if(weekend_free.Not())

# Penalize consecutive weekends with the same working status (aiming for alternating pattern)
ctx.model.add(same_status_penalty == 1).only_enforce_if([w1_free, w2_free])
ctx.model.add(same_status_penalty == 1).only_enforce_if([w1_free.Not(), w2_free.Not()])

return (
    Penalty(
        objective_id=self.id,
        name="every_second_weekend_free_penalty",
        expression=sum(penalties),
    ),
)
```

For each employee, the solver models whether each weekend is worked or free, and applies a penalty whenever two consecutive weekends have the same status, promoting a regular alternating rhythm.
