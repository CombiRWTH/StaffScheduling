--8<--
user-view/list-of-conditions.md:planned-shift
--8<--


### Implemented using Google's OR Tools

```python title="src/cp/constraints/planned_shifts.py"
variable = shift_assignment_variables[employee][day][exclusive_shift]
model.add(variable == 0)
```

For each planned shift we force the model to set the corresponding variable to 1, which assigns the shift.

This fuction is rather long since we also have check that no exclusive shifts are assigned to unauthorized employees.
