!!! note "Likelihood of Confusion"
    Different then the constraint [Free day after Night Shift Phase](./free-day-after-night-shift-phase.md).

--8<--
user-view/list-of-conditions.md:free-days-after-night-shift-phase
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/free_days_after_night_shift_phase.py"

model.add(penalty_var == 1).only_enforce_if(
    [night_var, next_day_var.Not(), after_next_day_var]
)
model.add(penalty_var == 0).only_enforce_if(night_var.Not())

penalties.append(penalty_var)
```

For each employee who is not hidden, we are looking at their work schedule over several days. A penalty will be applied under the following circumstances:

1. The employee works a night shift on one day.
2. The next day, the employee does not have any shifts scheduled (i.e., they have a day off).
3. On the day after that, the employee has a shift scheduled again.

If all these conditions are met, then a penalty is enforced.
