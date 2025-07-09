# Adding a New Objective to the Shift Scheduling System

This guide explains how to create and integrate a new objective into the shift scheduling system.

## Overview

Objectives define what the solver should optimize when generating shift plans. They can minimize undesirable outcomes (like overtime) or maximize desirable ones (like employee satisfaction). Multiple objectives can be combined with different weights to balance competing goals.

## Step 1: Create the Objective Class

Create a new Python file in the `cp/objectives/` directory:

```python
# cp/objectives/your_new_objective.py
from . import Objective
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel, IntVar
import logging


class YourNewObjective(Objective):
    KEY = "your-objective-key"  # Unique identifier for CLI usage

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initialize your objective with necessary data.

        Args:
            weight: Multiplier for this objective's contribution to the total objective
            employees: List of all employees
            days: List of dates in the planning period
            shifts: List of available shifts
        """
        super().__init__(weight, employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        """
        Define the objective logic using OR-Tools.
        This method is called during model creation.

        Returns:
            IntVar or linear expression: The objective term to be optimized
        """
        # Your objective implementation here
        # Must return an expression that will be minimized
        pass
```

## Step 2: Implement the Objective Logic

The `create` method is where you define your objective using OR-Tools CP-SAT API. The returned expression will be **minimized** by the solver:

```python
def create(self, model: CpModel, variables: dict[str, IntVar]):
    objective_terms = []

    for employee in self._employees:
        # Example: Minimize total shifts assigned
        employee_shifts = []
        for day in self._days:
            for shift in self._shifts:
                variable_key = EmployeeDayShiftVariable.get_key(employee, day, shift)
                if variable_key in variables:
                    employee_shifts.append(variables[variable_key])

        # Create an objective term for this employee
        employee_total = sum(employee_shifts)
        objective_terms.append(employee_total)

    # Return the weighted objective expression
    return sum(objective_terms) * self._weight
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
    ...
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
    cli = CLIParser([
        # ... existing constraints ...
        # ... existing objectives ...
        YourNewObjective,
    ])

    # ...

    objectives = [
        # ... existing objectives ...
        YourNewObjective(1.0, employees=employees, days=days, shifts=shifts),
    ]
```
