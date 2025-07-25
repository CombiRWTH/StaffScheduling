--8<--
user-view/list-of-conditions.md:user-free-day-after-night-shift-phase
--8<--

### Implemented using Google's OR Tools

```python title="src/cp/constraints/free_day_after_night_shift_phase.py"
model.add(day_tomorrow_variable == 0).only_enforce_if(
    [night_shift_today_variable, night_shift_tomorrow_variable.Not()]
)
```

For each non hidden employee and each day we enforce the next day to be free (`day_tomorrow_variable == 0`) if we got a night shift today, but not tomorrow, meaning the night shift phase ends.
