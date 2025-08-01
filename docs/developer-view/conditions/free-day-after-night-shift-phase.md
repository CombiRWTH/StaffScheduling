!!! note "Likelihood of Confusion"
    Different then the constraint [Free days after Night Shift Phase](./free-days-after-night-shift-phase-objective.md).

--8<--
user-view/list-of-conditions.md:user-free-day-after-night-shift-phase
--8<--

!!! Bug
    In the final presentation of our project a bug was found, possibly regarding this implementation. One other constraint could also be the source of this bug. More details can be found in this open [issue](https://github.com/CombiRWTH/StaffScheduling/issues/172).

### Implemented using Google's OR Tools

```python title="src/cp/constraints/free_day_after_night_shift_phase.py"
model.add(day_tomorrow_variable == 0).only_enforce_if(
    [night_shift_today_variable, night_shift_tomorrow_variable.Not()]
)
```

For each non hidden employee and each day we enforce the next day to be free (`day_tomorrow_variable == 0`) if we got a night shift today, but not tomorrow, meaning the night shift phase ends.
