# Adding a New Constraint to the Staff Scheduling System

This guide explains how to create and integrate a new constraint into the staff scheduling system.

## Overview

Constraints are rules that must be satisfied in the generated shift plans. They ensure legal requirements and company policies. Also, specific customer rules can be implemented.

## Step 1: Create the Constraint Class

Create a new Python file in the `cp/constraints/` directory:

```python
# cp/constraints/your_new_constraint.py
from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .constraint import Constraint


class YourNewConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "one-shift-per-day"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initialize your constraint with the necessary data.
        """
        super().__init__(employees, days, shifts)
        # Add any additional initialization here

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
 ):
        """
        Define the constraint logic using OR-Tools.
        This method is called during model creation.
        """
        # Your constraint implementation here
        pass
```

## Step 2: Implement the Constraint Logic

The `create` method is where you define your constraint using OR-Tools CP-SAT API:

```python
# an example constraint, which enforces that at most one shift can be assigned to an employee each day
def create(
    self,
    model: CpModel,
    shift_assignment_variables: ShiftAssignmentVariables,
    employee_works_on_day_variables: EmployeeWorksOnDayVariables,
):
    for employee in self._employees:
        for day in self._days:
            model.add_at_most_one(shift_assignment_variables[employee][day][shift] for shift in self._shifts)
```

## Step 3: Export the Constraint

Add your constraint to the `__init__.py` files:

```python
# cp/constraints/__init__.py
from .your_new_constraint import YourNewConstraint as YourNewConstraint
```
```python
# cp/__init__.py
from .constraints import (
    # ... existing imports ...
    YourNewConstraint as YourNewConstraint
)

```
## Step 4: Register in solve.py

Add your constraint to the main solver script:

```python
# solve.py
from cp import (
    # ... existing imports ...
    YourNewConstraint,
)

def main():
    # ...

    constraints = [
        # ... existing constraints ...
        YourNewConstraint(employees, days, shifts),
    ]

    # ...
```
