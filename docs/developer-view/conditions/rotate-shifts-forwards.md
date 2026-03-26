--8<--
user-view/list-of-conditions.md:rotate-shifts-forwards
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/objectives/rotate_shifts_forward.py"
# rotation_var is True when employee works from_shift on day1
    model.add_bool_and([from_shift_var, to_shift_var]).only_enforce_if(rotation_var)
    model.add_bool_or([from_shift_var.Not(), to_shift_var.Not()]).only_enforce_if(
        rotation_var.Not()
    )

return sum(possible_rotation_variables) * -1 * self.weight
```

Rotating the shifts forward is rewarded in the objective function.
