# How to Add a New Constraint

This guide explains how to add a new scheduling constraint to the project.

---

## 0. Create a new branch

## 1. Create a New Python Script

Add a new Python file inside `algorithm/building_constraints/`.

This file should contain:

### a) Load Function (optional)

If your constraint needs external parameters, define a function to load the data:

```python
import json

def load_free_shifts_and_vacation_days(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data
```


### b) Add Constraint Function

Define a function that:
- Accepts the model and variables
- Adds constraints to the model using OR-Tools
- Appends the constraint name to StateManager.state.constraints

Example:
```python
from ortools.sat.python import cp_model
import StateManager

def add_free_shifts_and_vacation_days(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    constraints: dict,
    num_shifts: int
) -> None:
    name_to_index = {employee['name']: idx for idx, employee in enumerate(employees)}

    if 'time_off' in constraints:
        for request in constraints['time_off']:
            employee_idx = name_to_index[request['name']]
            if "days_off" in request:
                for day in request['days_off']:
                    for s in range(num_shifts):
                        model.Add(shifts[(employee_idx, day, s)] == 0)
                    model.Add(shifts[(employee_idx, day, 2)] == 0)  # no night shift before vacation

            if "shifts_off" in request:
                for shift in request["shifts_off"]:
                    model.Add(shifts[(employee_idx, shift[0], shift[1])] == 0)

    StateManager.state.constraints.append("Free Shifts and Vacation Days")

```
Useful documentation for OR-Tools CP-SAT constraints can be found [here](https://developers.google.com/optimization/reference/python/sat/python/cp_model#cp_model.CpModel).

## 2. Create a JSON Configuration File
Define your constraint parameters in a JSON file inside the appropriate `cases/<case_id>/` folder.

Example:
```python
{
  "time_off": [
    {"name": "Pauline", "days_off": [1], "shifts_off": [[4, 2]]},
    {"name": "Marie", "days_off": [2]}
  ]
}
```

### 3. Import Your Functions in `solving.py`

Inside `algorithm/solving.py`, import your new constraint functions:
```python
from building_constraints.free_shifts_and_vacation_days import (
    load_free_shifts_and_vacation_days,
    add_free_shifts_and_vacatian_days,
)
````

### 4. Add Your Constraint to add_all_constraints

Extend the add_all_constraints() function by calling your load and add functions:

Example:
```python
free_shifts_and_vacation_days = load_free_shifts_and_vacation_days(
    f"./cases/{case_id}/free_shifts_and_vacation_days.json"
)
add_free_shifts_and_vacation_days(
    model,
    employees,
    shifts,
    free_shifts_and_vacation_days,
    num_shifts,
)
```

## Summary

| Step | Action |
|------|--------|
| 1    | Create a new script in `building_constraints/` |
| 2    | Write a `load_...()` function (if needed) and an `add_...()` function that modifies the model |
| 3    | Create a JSON file inside `cases/<case_id>/` with the constraint parameters |
| 4    | Import your functions in `solving.py` |
| 5    | Add your calls to `add_all_constraints()` |
