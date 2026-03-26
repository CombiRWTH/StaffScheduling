--8<--
user-view/list-of-conditions.md:min-rest-time
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/min_rest_time.py"
late_today = shift_assignment_variables[employee][day][self._shifts[Shift.LATE]]
early_tomorrow = shift_assignment_variables[employee][day + timedelta(1)][self._shifts[Shift.EARLY]]
not_early_tomorrow = early_tomorrow.Not()
model.add_implication(late_today, not_early_tomorrow)
```
We did not implement a solution that can vary the minimum rest time, but we just do not allow an early shift following a late shift, because then the rest time would only be 9 hours. If `late_today` is true, then also `not_early_tomorrow` needs to be true.
