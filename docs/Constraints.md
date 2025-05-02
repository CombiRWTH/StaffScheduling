# Constraints
This is an incomplete list of all constraints that we need keep track of in this project. 
An ideal constraint would contain a short description, an indicator on where this constrain
comes from (see "Sources of Information"), a mathematical representation, notes about
potential problems and a proposal how to implement such a constraint. For the latest, see 
[Documentation OR Tools](https://developers.google.com/optimization/reference/python/sat/python/cp_model#cp_model.CpModel).

_This list is not ideal._

## Sources of Information
1. Problemdefintion (pdf from Moodle)
2. Occupational Health and Safety Law (Arbeitsschutzgesetz) (pdf from Moodle)
3. Guidelines for Shift Work

## Idea for all soft constraints
It is not possible to set multiple maximize or minimize constraints. But we could think about the idea of combining all "soft constraints" to one minimize functions. Give a penalty for each shift that does not match a specific constraint (e.g. rotating fowards). Then we could build a global penalty function that we wanna minimize, where we can also weight the different constraints. 

## All Constraints

### Minimal Number of Staff (1)

![Staff_Requirements](Images/staff_requirements.png)

The above table shows the minimal number of stuff per day and per professional group.
If we have more stuff available:
1. Mo to Fr an additional "Zwischendienst" (T75)
2. "Zwischendienst" at the weekends
3. If there are enough people, Mo to Fr no "Zwischendienst" but one addtional stuff member to the first and second shift

### Free shifts or days (1)
Vacation days, free days on the weekend must remain free.
The day before a vacation day or a free weekend, there is no night shift allowed.
### Mathematical Representation
### Implementation Idea
Implementation should be easy. We just iterate through all free days and shifts and set the variables to zero:
```python
model.Add(shift == 0)
```

### Target Working hours (1)
per month a larger deviation than one day shift is not allowed (+/- 7.67 h)
addtionally in the next month this should be cons
!!! Problem here: CP Solver does only work with integers? Maybe scale hours up?
### Mathematical Representation
### Implementation Idea 
First get the current work time per employee depending on the shifts variables
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

### More free days for people with many night shifts (3.4)
Not sure if this is applicable for our case

### Shifts should "rotate forward" (3.5)
Meaning early, late, night and not night, late, early. This maximizes the time to rest between shifts. 

### Not to long shifts (3.9)
> Die Massierung von Arbeitstagen oder Arbeitszeiten auf einen Tag sollte begrenzt sein.

Essentially that means that longs shifts (12h plus) should be restricted.

### Weekend Rhythm (Kickoff Meeting)
Some kind of regularity for the free weekends


