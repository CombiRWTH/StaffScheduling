--8<--
user-view/list-of-conditions.md:min-rest-time
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/min_rest_time.py"
late_today = variables[
    EmployeeDayShiftVariable.get_key(
        employee, day, self._shifts[Shift.LATE]
    )
]
not_early_tomorrow = variables[
    EmployeeDayShiftVariable.get_key(
        employee, day + timedelta(1), self._shifts[Shift.EARLY]
    )
].Not()
model.add_implication(late_today, not_early_tomorrow)
```

If `late_today` is true, then also `not_early_tomorrow` needs to be true.
