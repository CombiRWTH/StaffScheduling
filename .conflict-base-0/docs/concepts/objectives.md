All objectiveds are located inside `src/cp/objectives/*.py`.
Each objective is implemented as a function that takes a `CpModel`[^1] object and adds the necessary constraints to it, while returning a returning a linear expression that represents the objective to be minimized.
Objectives are considered as soft constraints as they should be satisfied in the best way possible for a valid schedule.
For hard constraints, see the [Constraints](/concepts/constraints) chapter.

- [Free days near weekends](#free-days-near-weekends)
- [Minimize consecutive night shifts](#minimize-consecutive-night-shifts)
- [Minimize overtime/undertime](#minimize-overtimeundertime)
- [Not too many consecutive shifts](#not-too-many-consecutive-shifts)
- [Forward rotation of shifts](#forward-rotation-of-shifts)

# All Objectives

## Free days near weekends [^4]
Employees should have free days near weekends to ensure a better work-life balance.
This is a soft constraint that should be satisfied as much as possible.
Therefore, if an employee has a free day on a Friday to Monday, it is rewarded with a positive score in the objective function. A bonus is given when two or more consecutive free days are scheduled near the weekend.

```python title="src/cp/objectives/free_days_near_weekends.py"
if day.isoweekday() in [5, 6, 7]:
    model.add(day_today_variable == 0).only_enforce_if(
        free_today_day_variable
    )
    model.add(day_today_variable == 1).only_enforce_if(
        free_today_day_variable.Not()
    )
    if day + timedelta(1) in self._days:
        model.add(day_tomorrow_variable == 0).only_enforce_if(
            free_tomorrow_day_variable
        )
        model.add(day_tomorrow_variable != 0).only_enforce_if(
            free_tomorrow_day_variable.Not()
        )

        model.add_bool_and(
            [free_today_day_variable, free_tomorrow_day_variable]
        ).only_enforce_if(free_both_days_variable)
        model.add_bool_or(
            [
                free_today_day_variable.Not(),
                free_tomorrow_day_variable.Not(),
            ]
        ).only_enforce_if(free_both_days_variable.Not())
```

## Minimize consecutive night shifts

## Minimize overtime/undertime [^1]
Overtime and undertime are possible and acceptable, but they should be minimized as much as possible.
Therefore, the each minute of overtime or undertime is punished with a negative score in the objective function.

```python title="src/cp/objectives/minimize_overtime.py"
model.add_abs_equality(
    possible_overtime_variable,
    sum(possible_working_time) - target_working_time,
)
```

## Not too many consecutive shifts

## Forward rotation of shifts [^4]
Shifts should be rotated in a forward direction, meaning that the order of shifts should be from early to late, and not the other way around.
This is a soft constraint that should be satisfied as much as possible.
Therefore, rotating the shifts forward is rewarded with a positive score in the objective function.

```python title="src/cp/objectives/rotate_shifts_forward.py"
model.add_bool_and(
    [current_shift_variable, next_desired_shift_variable]
).only_enforce_if(rotation_variable)
model.add_bool_or(
    [
        current_shift_variable.Not(),
        next_desired_shift_variable.Not(),
    ]
).only_enforce_if(rotation_variable.Not())
```


[^1]: [OR Tools Documentation](https://developers.google.com/optimization/reference/python/sat/python/cp_model#cp_model.CpModel)
[^2]: Problem definition (PDF file from Moodle)
[^3]: Occupational Health and Safety Law (Arbeitsschutzgesetz) (PDF file from Moodle)
[^4]: Guidelines for shift work
