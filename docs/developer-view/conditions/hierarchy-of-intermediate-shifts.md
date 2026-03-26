--8<--
user-view/list-of-conditions.md:hierarchy-of-intermediate-shifts
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/hierarchy_of_intermediate_shifts.py"
# Guarantee that shifts on weekdays and weekends are assigned evenly
model.add(max_weekday - min_weekday <= 1)
model.add(max_weekend - min_weekend <= 1)

# Enforce the hierarchy: min(weekdays) <= max(weekends) + 1
model.add(max_weekday <= min_weekend + 1)
model.add(min_weekday >= max_weekend)
```
