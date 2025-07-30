--8<--
user-view/list-of-conditions.md:rotate-shifts-forwards
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/rotate_shifts_forward.py"
model.add_bool_and(
    [current_shift_variable, next_desired_shift_variable]
).only_enforce_if(rotation_variable)
model.add_bool_or(
    [
        current_shift_variable.Not(),
        next_desired_shift_variable.Not(),
    ]
).only_enforce_if(rotation_variable.Not())

...

return sum(possible_rotation_variables) * -1 * self.weight
```

Rotating the shifts forward is rewarded with a positive score in the objective function.
