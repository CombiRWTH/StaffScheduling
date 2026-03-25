--8<--
user-view/list-of-conditions.md:target-working-time
--8<--

!!! Bug There are blocked days and vacation days. Since vacation days are paid they should count towards the monthly target working time. Blocked days on the other hand should NOT count towards the monthly target working time, but they do in the current implementation. This was introduced to be able to find feasible solutions, but this has to be corrected eventually. The corresponding issue can be found [here](https://github.com/CombiRWTH/StaffScheduling/issues/249).

!!! Bug exclusive shifts do not count towards the total working time of an employee, since most of our instances do not have a feasible solution if they do. The corresponding issue can be found [here](https://github.com/CombiRWTH/StaffScheduling/issues/294).

### Implemented using Google's OR Tools

```python title="src/cp/constraints/target_working_time.py"
model.add(working_time_variable <= target_working_time + TOLERANCE_MORE)
model.add(working_time_variable >= target_working_time - TOLERANCE_LESS)
```

For employee create a variable representing the total work time in minutes which we restrict to being in [`target_working_time - TOLERANCE_LESS`, `target_working_time + TOLERANCE_MORE`].

!!! note

    Please note that we made an exception for the employee "Milburn Loremarie", because her `target-actual` time does not match the availabe shifts. She only has three not forbidden / not blocked days on which we need to work 30+ hours, this does not add up.
