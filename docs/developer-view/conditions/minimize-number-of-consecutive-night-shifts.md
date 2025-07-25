--8<--
user-view/list-of-conditions.md:min-num-of-cons-night-shifts
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/minimize_consecutive_night_shifts.py"

penalties.append(
    sum(possible_night_shift_phase_variables) * (self._weight**phase_length)
)
```

For each non hidden employee we create variables that show potential night shift phases, meaning multiple night shifts after each other. The sum of those (meaning the number how many of those are assigned) is weighed. For longer phase length the weight is increased exponentially, penaltising long night shifts quite heavily.
