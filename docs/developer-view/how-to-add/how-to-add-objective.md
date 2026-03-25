# Adding a New Objective to the Shift Scheduling System

This guide explains how to create and integrate a new objective into the shift scheduling system.

## Overview

Objectives define what the solver should optimize when generating shift plans. They can minimize undesirable outcomes (like overtime) or maximize desirable ones (like employee satisfaction). Multiple objectives can be combined with different weights to balance competing goals.

## Step 1: Create the Objective Class

Create a new Python file in the `cp/objectives/` directory:

```python
# cp/objectives/your_new_objective.py
from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class YourNewObjective(Objective):
    @property
    def KEY(self) -> str:
        """
        Returns a unique identifier of this class
        """
        return "a legacy artifact which usually carries the same name as the constraint."

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
 ):
        """
        Initialize your objective with the necessary data.

        Args:
        weight: Multiplier for this objective's contribution to the total objective
        employees: List of all employees
        days: List of dates in the planning period
        shifts: List of available shifts
        """
        super().__init__(weight, employees, days, shifts)
        # Add any additional initialization here

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
 ) -> LinearExpr:
        """
        Define the objective logic using OR-Tools.
        This method is called during model creation.

        Returns:
        linear expression = The objective term to be optimized
        """
        # Your objective implementation here
        # Must return an expression that will be minimized
        pass
```

## Step 2: Implement the Objective Logic

The `create` method is where you define your objective using OR-Tools CP-SAT API. The returned expression will be **minimized** by the solver:

```python
# an example objective, which encourages free days after a night shift phase
def create(
    self,
    model: CpModel,
    shift_assignment_variables: ShiftAssignmentVariables,
    employee_works_on_day_variables: EmployeeWorksOnDayVariables,
) -> LinearExpr:
    penalties: list[IntVar] = []

    for employee in self._employees:
        for day in self._days[:-2]:
            night_var = shift_assignment_variables[employee][day][self._shifts[Shift.NIGHT]]
            next_day_var = employee_works_on_day_variables[employee][day + timedelta(days=1)]
            after_next_day_var = employee_works_on_day_variables[employee][day + timedelta(days=2)]
            penalty_var = model.new_bool_var(f"free_days_after_night_{employee.get_key()}_{day}")

            model.add(penalty_var == 1).only_enforce_if([night_var, next_day_var.Not(), after_next_day_var])
            model.add(penalty_var == 0).only_enforce_if(night_var.Not())

            penalties.append(penalty_var)

    return cast(LinearExpr, sum(penalties) * self.weight)
```

## Step 3: Export the Objective

Add your objective to the `__init__.py` files:

```python
# cp/objectives/__init__.py
from .your_new_objective import YourNewObjective as YourNewObjective
```

```python
# cp/__init__.py
from .objectives import (
    # ... existing imports ...
    YourNewObjective as YourNewObjective
)
```

## Step 4: Register in solve.py

Add your objective to the main solver script:

```python
# solve.py
from cp import (
    # ... existing imports ...
    YourNewObjective,
)

def main():
    # ...

    constraints = [
        # ... existing constraints ...
        YourNewObjective(1.0, employees=employees, days=days, shifts=shifts),
    ]

    # ...
```
