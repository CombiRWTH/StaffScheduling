!!! note "Likelihood of Confusion"
    Different than the soft objective [Free days after Night Shift Phase](./free-days-after-night-shift-phase-objective.md).

--8<--
user-view/list-of-conditions.md:user-free-day-after-night-shift-phase
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/constraints/free_day_after_night_shift_phase.py"
# Enforce that all assignment variables tomorrow sum to 0 if a night shift was worked today but not tomorrow
constraint = ctx.model.add(sum(all_vars_tomorrow) == 0)
constraint.only_enforce_if([works_night_today, works_night_tomorrow.Not()])
```

For each employee and each day, we enforce the next day to be free (`sum(all_vars_tomorrow) == 0`) if they worked a night shift today, but not tomorrow, meaning their night shift phase has concluded.
