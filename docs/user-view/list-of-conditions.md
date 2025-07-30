We differentiate between two types of conditions:

- [**Constraints (Hard)**](#constraints) are essential requirements that must be satisfied for a valid schedule. For example, this includes factors like already planned vacation days.

- [**Objectives (Soft)**](#objectives) represent aspects that can be optimized but do not constitute strict requirements. An example of this would be minimizing the number of consecutive night shifts.

# Constraints
## Navigation Links
- [Free day after night shift phase](#free-day-after-night-shift-phase)
- [Max one shift per day](#max-one-shift-per-day)
- [Minimum rest time between shifts](#minimum-rest-time-between-shifts)
- [Minimum number of staff per shift](#minimum-number-of-staff-per-shift)
- [Target working time per month](#target-working-time-per-month)
- [Vacation days and free shifts](#vacation-days-and-free-shifts)

## All Constraints

### Free day after night shift phase [^4]
# --8<-- [start:user-free-day-after-night-shift-phase]
According to recommendations for the healthy organization of night and shift work, workers should have at least 24 hours of free time after a night shift.
This ensures that workers have sufficient rest after a night shift.
Therefore, if an employee works the night shift today and does not work the night shift tomorrow, they must take the day off.
# --8<-- [end:user-free-day-after-night-shift-phase]

### Max one shift per day
# --8<-- [start:user-max-one-shift-per-day]
Each employee is permitted to work only one shift per day. It is important to note that a night shift counts as part of the day on which it begins.
# --8<-- [end:user-max-one-shift-per-day]

### Minimum number of staff per shift [^2]
# --8<-- [start:min-number-of-staff-per-shift]
Each shift has a minimum required number of staff.
This is a hard constraint that must be met.
The goal is to ensure that the required number of qualified staff members are present for each shift.
Therefore, the total number of staff members assigned to a shift must be equal to the required number of staff for that shift. If there are additional ressources, the fourth
kind of shift, intermediate shifts, will be assigned.
Qualifications are not ordered, which means, that a "Fachkraft" (engl. skilled worker) cannot replace an "Azubi" (engl. trainee).

The required number of staff can be changed in `cases/{caseID}/minimal_number_of_staff.json`. Currently we use those numbers:

#### Fachkräfte
|       | Mo | Tu | We | Th | Fr | Sa | Su |
| ----- | -- | -- | -- | -- | -- | -- | -- |
| Early | 3  | 3  | 4  | 3  | 3  | 2  | 2  |
| Late  | 2  | 2  | 2  | 2  | 2  | 2  | 2  |
| Night | 2  | 2  | 2  | 2  | 2  | 1  | 1  |

#### Hilfskräfte
|       | Mo | Tu | We | Th | Fr | Sa | Su |
| ----- | -- | -- | -- | -- | -- | -- | -- |
| Early | 2  | 2  | 2  | 2  | 2  | 2  | 2  |
| Late  | 2  | 2  | 2  | 2  | 2  | 2  | 2  |
| Night | 0  | 0  | 0  | 0  | 0  | 1  | 1  |

#### Azubis
|       | Mo | Tu | We | Th | Fr | Sa | Su |
| ----- | -- | -- | -- | -- | -- | -- | -- |
| Early | 1  | 1  | 1  | 1  | 1  | 1  | 1  |
| Late  | 1  | 1  | 1  | 1  | 1  | 1  | 1  |
| Night | 0  | 0  | 0  | 0  | 0  | 0  | 0  |
# --8<-- [end:min-number-of-staff-per-shift]


### Target working time per month [^1]
# --8<-- [start:target-working-time]
Each employee has an individual monthly work target.
This target is considered a hard constraint because it must be met within a certain range.
A maximum deviation of one day shift is allowed (±7.67 hours), but this is minimized by the [objective](#minimize-overtime-and-undertime) function to ensure minimal overtime/undertime.
Therefore, the total working time must fall within the range of all possible shift combinations and the target working time range.
# --8<-- [end:target-working-time]


### Vacation days and free shifts [^1]
# --8<-- [start:vacation-days-and-free-shifts]
Vacation days must remain free, and the day before a vacation day no night shift is allowed. This vacation days are automatically read from the database / TimeOffice.
# --8<-- [end:vacation-days-and-free-shifts]


### Hierarchy of Intermediate Shifts [^2]
# --8<-- [start:hierarchy-of-intermediate-shifts]
Intermediate shifts are assigned once the minimum staffing requirement is met and sufficient personnel resources are available. The assignment of these shifts follows a specific pattern: we prioritize one shift per day for each weekday, followed by weekend shifts. After that, we aim to assign two shifts on weekdays, and then again on weekends.

In cases where two or more intermediate shifts are scheduled in a single day, the station management will convert them into early and late shifts, as these options tend to be more popular among staff. However, it’s important to note that this conversion process is currently manual and not automated by our application.
# --8<-- [end:hierarchy-of-intermediate-shifts]


### Planned Shifts [^2]
# --8<-- [start:planned-shifts]
Planned shifts are shifts that are already assigned in TimeOffice. All planned shifts are hard constraints, meaning they are automatically assigned and there will be not solution without those.
An example would be the special shift (Z60), which can be assigned to an employee each Thursday in TimeOffice and then also be assigned in our application.
# --8<-- [end:planned-shifts]


### Rounds (Visiten) [^2]
# --8<-- [start:rounds]
In the early shift, at least one employee must conduct a round.
Employees need to have a proper qualification to conduct a round.
Therefore, at least one qualified employee needs to be assigned to an early shift on workdays.
# --8<-- [end:rounds]

### Minimum Rest Time [^3]
# --8<-- [start:min-rest-time]
According to Occupational Health and Safety Law (Arbeitsschutzgesetz) the minimum rest time for normal employees need to be at least 11 hours. In hospitals there can be exception to this rule.
We did not implement a solution that can vary the minimum rest time, but we just do not allow an early shift following a late shift, because then the rest time would only be 9 hours.
# --8<-- [end:min-rest-time]



# Objectives
All the objectives are combined (added) to a total objective function
that the minimum will be approximated from. Each objective has a weight by which one
could change the importance of a specific objective. Those weights are set in `src/cp/solve.py` and should be always greater or equal to $1.0$:

``` python
objectives = [
    FreeDaysNearWeekendObjective(10.0, employees, days),
    MinimizeConsecutiveNightShiftsObjective(2.0, employees, days, shifts),
    MinimizeHiddenEmployeesObjective(100.0, employees, days, shifts),
    MinimizeOvertimeObjective(4.0, employees, days, shifts),
    NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, 1.0, employees, days),
    RotateShiftsForwardObjective(1.0, employees, days, shifts),
]
```

## Navigation Links
- [Free days near weekend](#free-days-near-weekend)
- [Minimize number of consecutive night shifts](#Minimize-number-of-consecutive-night-shifts)
- [Minimize hidden employees](#minimize-hidden-employees)
- [Minimize overtime and undertime](#minimize-overtime-and-undertime)
- [Not too many consecutive working days](#not-too-many-consecutive-working-days)
- [Rotate shifts forwards](#Rotate-shifts-forwards)

## All Objectives

### Free days near weekend [^4]
A schedule is found that increases the number of free days near weekends for employees.

### Minimize number of consecutive night shifts [^4]
The aim is to minimize the length of night shift phases, defined as consecutive night shifts occurring one after another.

### Minimize hidden employees
Hidden employees are employees that do not exist. Shifts should only be assigned to
them if otherwise a valid solution cannot be found. This for example happens, if there
is a shortage on skilled employees.
Hidden employees do not have the same rules as real employees, they can work multiple
shifts per day. They should indicate how many employees / how many shifts are missing
to get a valid schedule.

### Minimize overtime and undertime
The goal is to minimize both overtime and undertime to ensure a fair and equitable distribution of work among employees. Hard limits are established, as outlined in the section on [Target Working Time per Month](#target-working-time-per-month).

### Not too many consecutive working days [^4]
The aim is to minimize consecutive working days that extend to six or more, in order to prevent prolonged periods of work.


### Rotate shifts forwards [^4]
The forward shift rotation constraint requires employees to transition from earlier shifts to later shifts, promoting better health and reducing fatigue.

An employee's weekly schedule should progress from early shifts to late shifts and then to night shifts, not the other way around.


[^1]: [OR Tools Documentation](https://developers.google.com/optimization/reference/python/sat/python/cp_model#cp_model.CpModel)
[^2]: Problem definition (as this was a lab course at RWTH)
[^3]: Occupational Health and Safety Law (Arbeitsschutzgesetz) (PDF file from Moodle)
[^4]: Guidelines for shift work
