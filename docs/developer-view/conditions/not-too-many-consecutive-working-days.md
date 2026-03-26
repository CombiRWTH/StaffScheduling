--8<--
user-view/list-of-conditions.md:min-working-phases
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/not_too_many_consecutive_days.py"

        possible_overwork_variables.append(day_phase_variable)

return sum(possible_overwork_variables) * self.weight
```

For each employee we create variables that show potential day phases that are longer than `MAX_CONSECUTIVE_DAYS`, which is defined in `src/cp/constants.py`.

!!! note

    Similar to [Minimize Consecutive Night Shifts](/docs/developer-view/conditions/minimize-number-of-consecutive-night-shifts.md) but without the expontential relation to the length of the phase, allowing longer phases compared to night shifts.
