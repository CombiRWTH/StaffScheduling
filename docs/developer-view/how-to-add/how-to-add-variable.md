# How to Add & Use Variables in CP-SAT

This guide explains how decision variables and helper variables are created and utilized within the CP-SAT solver.

---

## Two Categories of Variables

In the Staff Scheduling solver, variables fall into two distinct categories:

| Category | Defined In | Purpose |
|---|---|---|
| **Primary Assignment Variables** | [`src/scheduling/solver/cp_sat/variables.py`](file:///c:/Users/jonas/Dev/StaffScheduling/src/scheduling/solver/cp_sat/variables.py) | Represents the core roster decisions: whether an employee is assigned to a shift slot. |
| **Auxiliary / Helper Variables** | Inside individual constraints and objectives | Intermediate integer or Boolean variables used to linearize complex logic (e.g. streaks, overtime, day indicators). |

---

## 1. Primary Assignment Variables

The core search space is defined by Boolean assignment variables stored on `ctx.assignment_variables`:

$$x_{e, u, d, s, l} \in \{0, 1\}$$

Where each variable is indexed by an **`AssignmentVariableKey`** tuple:

```python
AssignmentVariableKey = tuple[
    int,         # employee_id
    int,         # planning_unit_id
    date,        # assignment_date
    ShiftId,     # shift_id
    StaffLevel,  # staff_level (qualification role filled)
]
```

### Slot Pruning & Eligibility
Variables are **not** created blindly for every combination of employee, date, and shift. In [`create_assignment_variables`](file:///c:/Users/jonas/Dev/StaffScheduling/src/scheduling/solver/cp_sat/variables.py), the generator calls:

```python
staff_levels = eligible_staff_levels_for_assignment_slot(
    employee=employee,
    planning_unit_id=planning_unit_id,
    assignment_date=assignment_date,
    shift_id=shift_id,
    index=ctx.index,
)
```

If an employee lacks the qualification for a role, or does not belong to the station, no variable is created. This drastically reduces the size of the search space.

### Accessing Assignment Variables in Constraints/Objectives

```python
# Iterate through all assignment variables
for (employee_id, unit_id, assignment_date, shift_id, role), var in ctx.assignment_variables.items():
    # Filter by employee, date, or shift
    if assignment_date.weekday() == 6:  # Sundays
        ...
```

---

## 2. Creating Auxiliary / Helper Variables

When writing a constraint or objective, you often need helper variables to represent derived states (such as *"Did employee E work on day D?"* or *"How many hours of overtime did employee E accrue?"*).

Helper variables are created directly on `ctx.model`.

### Pattern A: Boolean Indicator (e.g. "Works on Day")

To create a Boolean variable `w[e, d]` that is `1` if an employee works *any* shift on day $d$, and `0` otherwise:

```python
# Create the boolean indicator
works_on_day = ctx.model.new_bool_var(f"works_emp{employee_id}_{date_str}")

# shift_vars contains all shift variables for that employee on that date
shift_vars = [var for (_e, _u, d, _s, _l), var in ctx.assignment_variables.items() if d == target_date]

# works_on_day == max(shift_vars) (True if at least one shift is True)
ctx.model.add_max_equality(works_on_day, shift_vars)
```

### Pattern B: Bounded Integer (e.g. Overtime Minutes)

To compute non-linear values like positive overtime ($\max(0, \text{worked} - \text{target})$):

```python
# 1. Total minutes worked
total_minutes = sum(shift.duration_minutes * var for shift, var in employee_shifts)

# 2. Overtime variable with tight upper bound
max_possible_overtime = 50 * 60  # e.g. 50 hours in minutes
overtime_var = ctx.model.new_int_var(0, max_possible_overtime, f"overtime_emp{employee_id}")

# 3. Enforce: overtime_var >= total_minutes - target_minutes
ctx.model.add(overtime_var >= total_minutes - target_minutes)
```

### Pattern C: Conditional Enforcement (`only_enforce_if`)

To model "If employee works Night shift on Day $D$, then they cannot work Early shift on Day $D+1$":

```python
night_var = ctx.assignment_variables[(emp_id, unit_id, day_d, night_shift_id, role)]
early_next_day_var = ctx.assignment_variables[(emp_id, unit_id, day_d_plus_1, early_shift_id, role)]

# If night_var is 1, early_next_day_var must be 0
ctx.model.add(early_next_day_var == 0).only_enforce_if(night_var)
```

---

## Best Practices for CP-SAT Variables

1. **Tight Bounds:** Always give integer variables the smallest possible lower and upper bounds (`[0, max_minutes]` rather than `[0, 1000000]`). Tight bounds dramatically speed up CP-SAT domain propagation.
2. **Descriptive Names:** Always supply a unique, descriptive string name when calling `new_bool_var("...")` or `new_int_var(...)`. These names appear in CP-SAT logs and make conflict debugging straightforward.
3. **Avoid Redundant Variables:** If a quantity can be represented as a linear combination of existing variables (`sum(x_i)`), do not introduce a new intermediate variable unless required for conditional enforcement (`only_enforce_if`) or non-linear operators (`add_max_equality`).
