# Adding a New Constraint to the Staff Scheduling System

This guide explains how to create and integrate a new constraint into the shift scheduling system.

## Overview

Constraints are rules that must be satisfied in the generated shift plans. They ensure legal requirements, company policies, and employee preferences are respected.

## Step 1: Create the Constraint Class

Create a new Python file in the `cp/constraints/` directory:

```python
# cp/constraints/your_new_constraint.py
from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel
import logging


class YourNewConstraint(Constraint):
    KEY = "your-constraint-key"  # Unique identifier for CLI usage

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initialize your constraint with necessary data.
        """
        super().__init__(employees, days, shifts)
        # Add any additional initialization here

    def create(self, model: CpModel, variables: dict[str, Variable]):
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
def create(self, model: CpModel, variables: dict[str, Variable]):
    for employee in self._employees:
        for day in self._days:
            # Example: Limit shifts per week
            week_shifts = []
            for shift in self._shifts:
                variable_key = EmployeeDayShiftVariable.get_key(employee, day, shift)
                if variable_key in variables:
                    week_shifts.append(variables[variable_key])

            # Add constraint to model
            model.add(sum(week_shifts) <= 5)  # Max 5 shifts per week
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
    ...
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
    cli = CLIParser([
        # ... existing constraints ...
        YourNewConstraint,
    ])

    # ...

    constraints = [
        # ... existing constraints ...
        YourNewConstraint(employees, days, shifts),
    ]
```
