--8<--
user-view/list-of-conditions.md:target-working-time
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/target_working_time.py"
target_working_time = employee.get_available_working_time()
model.add(working_time_variable <= target_working_time + TOLERANCE_MORE)
model.add(working_time_variable >= target_working_time - TOLERANCE_LESS)
```

For each non hidden employee create a variable representing the total work time in minutes which we restrict to being in [`target_working_time + TOLERANCE_LESS`, `target_working_time + TOLERANCE_MORE`].
The target working time is the difference between the "SOLL"-Time given in TimeOffice and the "IST"-Time in TimeOffice. Those are exported from the database and stored in `cases/{case_id}/target_working_minutes.json` as `target` and `actual`.

!!! note

    Please note that we made an exception for the employee "Milburn Loremarie", because her `target-actual` time does not match the availabe shifts. She only has three not forbidden / not blocked days on which we need to work 30+ hours, this does not add up.
