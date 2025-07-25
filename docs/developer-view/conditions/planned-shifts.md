--8<--
user-view/list-of-conditions.md:planned-shift
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/planned_shifts.py"
variable_key = EmployeeDayShiftVariable.get_key(employee, day, shift)
if variable_key in variables:
    model.add(variables[variable_key] == 1)
```

For each planned shift we force the model to set the corresponding variable to 1, which assigns the shift.
