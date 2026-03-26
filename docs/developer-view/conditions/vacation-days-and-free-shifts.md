--8<--
user-view/list-of-conditions.md:vacation-days-and-free-shifts
--8<--

### Implemented using Google's OR Tools

This might be one of the easiest constraints. If an employee is unavailable for a day or shift, the corresponding variables `EmployeeDayVariable` or `EmployeeDayShiftVariable` is set to `0` (not assigned).

```python title="src/cp/constraints/vacation_days_and_shifts.py"
if employee.unavailable(day):
    day_variable = employee_works_on_day_variables[employee][day]
    model.add(day_variable == 0)
```

```python title="src/cp/constraints/vacation_days_and_shifts.py"
if employee.unavailable(day, shift):
    shift_variable = shift_assignment_variables[employee][day][shift]
    model.add(shift_variable == 0)
```
