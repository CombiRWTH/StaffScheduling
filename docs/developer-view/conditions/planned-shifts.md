--8<--
user-view/list-of-conditions.md:planned-shift
--8<--

!!! Bug
    In the final presentation of our project a bug was found, possibly regarding this implementation. One other constraint could also be the source of this bug. More details can be found in this open [issue](https://github.com/CombiRWTH/StaffScheduling/issues/172).


### Implemented using Google's OR Tools

```python title="src/cp/constraints/planned_shifts.py"
variable_key = EmployeeDayShiftVariable.get_key(employee, day, shift)
if variable_key in variables:
    model.add(variables[variable_key] == 1)
```

For each planned shift we force the model to set the corresponding variable to 1, which assigns the shift.
