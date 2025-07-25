--8<--
user-view/list-of-conditions.md:rounds
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/rounds_in_early_shift.py"
early_shift_variables = [
    variables[
        EmployeeDayShiftVariable.get_key(
            employee, day, self._shifts[Shift.EARLY]
        )
    ]
    for employee in qualified_employees
]

model.add_at_least_one(early_shift_variables)
```

For each day we collect the early shift variables of all qualified employee (see `cases/{case_id}/general_settings.json`) and restrict the model to solution where at least one of them are true.
