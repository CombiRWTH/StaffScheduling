# Constraints
This is an incomplete list of all constraints that we need keep track of in this project.
An ideal constraint would contain a short description, an indicator on where this constraint
comes from (see "Sources of Information"), a mathematical representation, notes about
potential problems and a proposal on how to implement such a constraint. For the latest documentation, see
[Documentation OR Tools](https://developers.google.com/optimization/reference/python/sat/python/cp_model#cp_model.CpModel).

## Sources of Information
1. Problem definition (PDF file from Moodle)
2. Occupational Health and Safety Law (Arbeitsschutzgesetz) (PDF file from Moodle)
3. Guidelines for shift work

## Idea for all soft constraints
It is not possible to set multiple maximize or minimize constraints but we could think about combining all "soft constraints" to one objective function that can be minimized. Given a penalty for each shift that does not match a specific constraint (e.g. rotating foward), we could build a global objective function that we want to minimize, enabling us to also assign a weight to the different constraints.

## All Constraints

### Minimal Number of Staff (1)

![Staff_Requirements](Images/staff_requirements.png)

The above table shows the minimal number of staff per day and per professional group.
If we have more staff available:


1. Mo - Fr an additional "Zwischendienst" (T75)
2. "Zwischendienst" on the weekends
3. If there are enough people, Mo - Fr no "Zwischendienst" but one addtional staff member to the first and second shift

### Free shifts or days (1)
Vacation days and free days on the weekend must remain free.
The day before a vacation day or a free weekend no night shift is allowed.

- **Mathematical Representation:**
- **Implementation Idea:** Implementation should be easy. We just iterate through all free days and shifts and set the variables to zero:
```python
model.Add(shift == 0)
```

### Target Working hours (1)
Per month a maximum deviation of one day shift is allowed (+/- 7.67 h).

Addtionally in the next month this should be considered.
!!! Problem here: CP Solver does only work with integers? Maybe scale hours up?

- **Mathematical Representation:**
- **Implementation Idea:** First get the current work time per employee depending on the shifts variables
```python
model.Add(current_work_time_per_employee <= target_minuts + 7.67 * 60)
model.Add(current_work_time_per_employee >= target_minuts - 7.67 * 60)
```

### Minimize Number of Consecutive Night Shifts (3.1)

### 24h no shift after phase of Night Shifts (3.2)

### Free days near weekend (3.3)
Free days should come in pairs (two) and include at least one weekend day:

- Friday and Saturday
- Saturday and Sunday
- Sunday and Monday

### Shifts should "rotate forward" (3.5)
Meaning early, late, night and not night, late, early. This maximizes the time to rest between shifts.

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

## Constraints that might not apply in our case

### More free days for people with many night shifts (3.4) (?)
Not sure if this is applicable for our case

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

### Not to long shifts (3.9) (?)
> Die Massierung von Arbeitstagen oder Arbeitszeiten auf einen Tag sollte begrenzt sein.
Essentially that means that longs shifts (12h plus) should be restricted. But I think there are not 12h shift in our case.
