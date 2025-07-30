--8<--
user-view/configuration/index.md:only-json-files-note
--8<--

### Weights Configuration

!!! warning
    Please note that the weights assigned to objectives must be greater than or equal to 1.

In our application, users can adjust the importance of various objectives within the general objective function to optimize scheduling and resource allocation. This configuration is managed in the `srs/solve.py` file.

The objectives are defined as follows:

```python
objectives = [
    FreeDaysNearWeekendObjective(10.0, employees, days),
    MinimizeConsecutiveNightShiftsObjective(2.0, employees, days, shifts),
    MinimizeHiddenEmployeesObjective(100.0, employees, days, shifts),
    MinimizeOvertimeObjective(4.0, employees, days, shifts),
    NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, 1.0, employees, days),
    RotateShiftsForwardObjective(1.0, employees, days, shifts),
    MaximizeEmployeeWishesObjective(3.0, employees, days, shifts),
    FreeDaysAfterNightShiftPhaseObjective(3.0, employees, days, shifts),
]
```

Each objective is assigned a weight represented by a numerical value (e.g., `10.0`, `2.0`, etc.). By changing these numbers in the codebase, users can effectively prioritize specific objectives according to their operational needs and preferences.
