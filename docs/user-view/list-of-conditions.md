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
According to recommendations for the healthy organization of night and shift work, workers should have at least 24 hours of free time after a night shift.
This ensures that workers have sufficient rest after a night shift.
Therefore, if an employee works the night shift today and does not work the night shift tomorrow, they must take the day off.

### Max one shift per day
Each employee is permitted to work only one shift per day. It is important to note that a night shift counts as part of the day on which it begins.

### Minimum rest time between shifts [^3]
 @todo !!! STILL MISSING !!! We are not quite sure yet, if we use a flexible rest
 time between shifts or if we use 9 hours or 10...

### Minimum number of staff per shift [^2]
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


### Target working time per month [^1]

Each employee has an individual monthly work target.
This target is considered a hard constraint because it must be met within a certain range.
A maximum deviation of one day shift is allowed (±7.67 hours), but this is minimized by the [objective](#minimize-overtime-and-undertime) function to ensure minimal overtime/undertime.
Therefore, the total working time must fall within the range of all possible shift combinations and the target working time range.


### Vacation days and free shifts [^1]

Vacation days must remain free, and the day before a vacation day no night shift is allowed.
There are also forbidden days (shifts), which are simply days (shifts) on which a person is not allowed to work, e.g. "Miss Jane Doe is not allowed to work night shifts" or "John Q. Citizen" does not work on Fridays".


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

### Free days near weekend
A schedule is found that increases the number of free days near weekends for employees.

### Minimize number of consecutive night shifts
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

### Not too many consecutive working days
The aim is to minimize consecutive working days that extend to six or more, in order to prevent prolonged periods of work.


### Rotate shifts forwards
The forward shift rotation constraint requires employees to transition from earlier shifts to later shifts, promoting better health and reducing fatigue.

An employee's weekly schedule should progress from early shifts to late shifts and then to night shifts, not the other way around.


[^1]: [OR Tools Documentation](https://developers.google.com/optimization/reference/python/sat/python/cp_model#cp_model.CpModel)
[^2]: Problem definition (PDF file from Moodle)
[^3]: Occupational Health and Safety Law (Arbeitsschutzgesetz) (PDF file from Moodle)
[^4]: Guidelines for shift work
