--8<--
user-view/list-of-conditions.md:user-max-one-shift-per-day
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/max_one_shift_per_day.py"
for employee in self._employees:
    if employee.hidden:
        continue

    for day in self._days:
        model.add_at_most_one(
            variables[EmployeeDayShiftVariable.get_key(employee, day, shift)]
            for shift in self._shifts
        )
```

For each non hidden employee, for each day, allow at most one of the shift variables.
