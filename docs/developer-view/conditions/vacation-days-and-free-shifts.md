--8<--
user-view/list-of-conditions.md:vacation-days-and-free-shifts
--8<--

### Implemented using Google's OR-Tools

In the modern architecture, vacations, sick leaves, and blocked days are unified into the `AvailabilitiesConstraint`:

```python title="src/scheduling/solver/cp_sat/constraints/availabilities_constraint.py"
# For any date where an employee is marked unavailable, enforce 0 assignments
for (employee_id, unavailable_date), variables in unavailable_variables.items():
    ctx.model.add(sum(variables) == 0).with_name(
        f"unavailable_emp_{employee_id}_{unavailable_date:%Y%m%d}"
    )
```

If an employee has an approved vacation day, sickness, or a blocked day in TimeOffice (`Availability` domain model), the solver collects all assignment variables for that employee on that date and forces their sum to `0`.
