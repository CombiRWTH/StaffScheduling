--8<--
user-view/list-of-conditions.md:min-over-and-undertime
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/minimize_overtime.py"
    model.add_abs_equality(
        possible_overtime_variable,
        sum(possible_working_time) - target_working_time,
    )
    ...
return sum(possible_overtime_absolute_variables) * self._weight
```

Each minute of overtime or undertime is punished with a negative score in the objective function.
