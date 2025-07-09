All constraints are located inside `src/cp/constraints/*.py`.
Each constraint is implemented as a function that takes a `CpModel`[^1] object and adds the necessary constraints to it.
Constraints are considered as hard constraints as they must be satisfied for a valid schedule.
For soft constraints, see the [Objectives](/concepts/objectives) chapter.

- [Free day after night shift phase](#free-day-after-night-shift-phase)
- [Max one shift per day](#max-one-shift-per-day)
- [Minimum rest time between shifts](#minimum-rest-time-between-shifts)
- [Minimum number of staff per shift](#minimum-number-of-staff-per-shift)
- [Rounds in early shift](#rounds-in-early-shift)
- [Target working time per month](#target-working-time-per-month)
- [Vacation days and free shifts](#vacation-days-and-free-shifts)

# All Constraints

## Free day after night shift phase [^4]

According to recommendations for the healthy organization of night and shift work, workers should have at least 24 hours of free time after a night shift.
This ensures that workers have sufficient rest after a night shift.
Therefore, if an employee works the night shift today and does not work the night shift tomorrow, they must take the day off.

```python title="src/cp/constraints/free_day_after_night_shift_phase.py"
model.add(day_tomorrow_variable == 0).only_enforce_if(
    [night_shift_today_variable, night_shift_tomorrow_variable.Not()]
)
```

## Max one shift per day

## Minimum rest time between shifts [^3]

## Minimum number of staff per shift [^2]

Each shift has a minimum required number of staff.
This is a hard constraint that must be met.
The goal is to ensure that the required number of qualified staff members are present for each shift.
Therefore, the total number of staff members assigned to a shift must be greater than or equal to the required number of staff for that shift.

```python title="src/cp/constraints/min_staffing.py"
model.add(sum(potential_working_staff) >= min_staffing)
```

![Staff_Requirements](/images/staff_requirements.png)
/// caption
Staff requirements per weekday and professional group.
///

## Rounds in early shift [^2]

In the early shift, at least one employee must conduct a round.
Employees need to have a proper qualification to conduct a round.
Therefore, at least one qualified employee needs to be assigned to an early shift on workdays.

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

## Target working time per month [^1]

Each employee has an individual monthly work target.
This target is considered a hard constraint because it must be met within a certain range.
A maximum deviation of one day shift is allowed (±7.67 hours), but this is minimized by the [objective](/concepts/objectives/#minimize-overtimeundertime) function to ensure minimal overtime/undertime.
Therefore, the total working time must fall within the range of all possible shift combinations and the target working time range.

```python title="src/cp/constraints/target_working_time.py"
working_time_variable = model.new_int_var_from_domain(
    working_time_domain, f"working_time_e:{employee.get_id()}"
)

model.add(sum(possible_working_time) == working_time_variable)
model.add(working_time_variable <= target_working_time + TOLERANCE_MORE)
model.add(working_time_variable >= target_working_time - TOLERANCE_LESS)
```

## Vacation days and free shifts [^1]

Vacation days must remain free, and the day before a vacation day no night shift is allowed.
Therefore, if an employee has a vacation day or a free shift, the corresponding shift variable must be set to zero. Also considering the night shift the day before a vacation day or free shift.

```python title="src/cp/constraints/vacation_days_and_free_shifts.py"
if employee.has_vacation(day.day):
    model.add(day_variable == 0)

    if day.day > 1:
        model.add(night_shift_variable == 0)

if employee.has_vacation(day.day, shift.get_id()):
    model.add(shift_variable == 0)
```
<!--

## All Constraints

### Minimal Number of Staff (1)

1. Mo - Fr an additional "Zwischendienst" (T75)
2. "Zwischendienst" on the weekends
3. If there are enough people, Mo - Fr no "Zwischendienst" but one addtional staff member to the first and second shift


### Weekend Rhythm (Kickoff Meeting)
Some kind of regularity for the free weekends

### No Late to Early Shifts (from Rest Time (2) (§5 (1,2)))
This is the essence of the "Rest Time Constraint" below adjusted to our case.
No Late to Early Shifts means that it is not allowed that an early shift follows a late shift, because then the rest time would not be long enough.

### At least 15 Sundays free per year (2) (§11 (1))
That is a compensation for the work on sundays and holidays

### Replacement day when working on Sunday/Holiday (2) (§11 (2))
- Work on Sunday: Free compensation day in the next two weeks
- Work on a Holiday: Free compensation day in the next 8 weeks


### More free days for people with many night shifts (3.4)
### !!! This constraint may lead to the case that the night shift worker has too much free days, we need to add more constraint to adjust it
This constraint is feasible for our project, we achieve it by the following way:
1. Calculate the night shift times for each worker and denote it as "num_night_shifts" in the model
2. Calculate the free days for each worker and denote it as "num_rest_days" in the model
3. Calculate "surplus" using the following code
```python
model.Add(surplus == num_rest_days - num_night_shifts)
```
4. Add the constraint to maximaize the surplus to ensure night shift worker has more free days


### Rest Time (2) (§5 (1,2))
11 hours of rest time between shift. There is an exception for employees in the hospital: there it could only be 10 hours, if this is balanced during the current month by one rest time with 12 hours.
For us it is easier to check if there are always two empty shifts between two working shifts. This is automatically the case for almost all cases, by restricting the employees to only have one shift per day. There are three cases where this "one-per-day" restriction does not cover the "Rest Time" Condition:

- Night to Early: Less than 11 hours, but covered by the "24h rest time after night shift"
- Night to Late: Less than 11 hours, but covered by the "24h rest time after night shift"
- Late to Early: Here we only have 9 hours of rest time. **That is why we must not allow this combination!**

### Rest Time On Call Duty (2) (§5 (3)) (?)
On Call Duty is someone who is resting at that shift, but we mark him as "On Call Duty", which means he needs to work only if there is an emergency, and the lost rest time will be compensated later.

1. We need another parameter - "lost rest time" for the worker, to calculate the rest time to be compensated.
2. The working hours during the "On Call Duty" can't be longer than 5.5 hours, since the rest time for a hospital worker is a maximum of 11 hours.
**Do we have "On Call Duty"?**

### Not to long shifts (3.9)
This constraint means: Die Massierung von Arbeitstagen oder Arbeitszeiten auf einen Tag sollte begrenzt sein.

The way we achieve it is to create a window to watch if every worker consecutive works in 5 days, then we punish the situation that worker consevutive works.
When in the window of 5 days, the worker consecutive works, we set the overwork to 1, and we try to minimize the value of overwork
```python
window = [work[(n, d + i)] for i in range(MAX_CONSECUTIVE_WORK_DAYS + 1)]
model.Add(sum(window) == MAX_CONSECUTIVE_WORK_DAYS + 1).OnlyEnforceIf(overwork)
model.Add(sum(window) != MAX_CONSECUTIVE_WORK_DAYS + 1).OnlyEnforceIf(overwork.Not())
```

Essentially that means that longs shifts (12h plus) should be restricted. -->

[^1]: [OR Tools Documentation](https://developers.google.com/optimization/reference/python/sat/python/cp_model#cp_model.CpModel)
[^2]: Problem definition (PDF file from Moodle)
[^3]: Occupational Health and Safety Law (Arbeitsschutzgesetz) (PDF file from Moodle)
[^4]: Guidelines for shift work
