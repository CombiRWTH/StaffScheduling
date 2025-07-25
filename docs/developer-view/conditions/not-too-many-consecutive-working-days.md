--8<--
user-view/list-of-conditions.md:min-working-phases
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/not_too_many_consecutive_days.py"

        possible_overwork_variables.append(day_phase_variable)

return sum(possible_overwork_variables) * self.weight
```

For each non hidden employee we create variables that show potential day phases that are longer than `max_consecutive_shifts`, meaning working multiple days after each other. `max_consective_shifts` is set to `MAX_CONSECUTIVE_NIGHTS` which is defined as `5` in `src/solve.py`.
The sum of those variables corresponding to phases is weighed and used as penalty. For longer phase length the weight is increased exponentially, penaltising long night shifts quite heavily.

!!! note

    Similar to [Minimize Consecutive Night Shifts](/docs/developer-view/conditions/minimize-number-of-consecutive-night-shifts.md) but without the expontential relation to the length of the phase, allowing longer phases compared to night shifts.
