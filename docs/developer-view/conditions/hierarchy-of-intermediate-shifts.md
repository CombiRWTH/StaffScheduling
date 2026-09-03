--8<--
user-view/list-of-conditions.md:hierarchy-of-intermediate-shifts
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/constraints/hierarchy_of_intermediate_shifts.py"
# Guarantee that shifts on weekdays and weekends are assigned evenly within ±1
ctx.model.add(max_wd - min_wd <= 1)
ctx.model.add(max_we - min_we <= 1)

# Enforce the hierarchy: weekdays must be filled before weekends are assigned
ctx.model.add(max_we <= min_wd)
ctx.model.add(max_wd <= min_we + 1)
```

For each station and calendar week, intermediate shifts are distributed evenly across weekdays (Monday–Friday) before weekend shifts (Saturday–Sunday) are scheduled.
