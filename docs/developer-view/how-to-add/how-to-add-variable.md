# Adding a New Variable to the Shift Scheduling System

This guide explains how to create and integrate a new variable into the shift scheduling system.

## Overview

Variables are the decision elements that the solver can set when creating a schedule. They represent choices like "Does employee X work shift Y on day Z?"
## Why Variable Classes?
- **Consistent Referencing**: Variables are used in multiple constraints and objectives. Having dedicated classes makes it easier to reference them consistently instead of needing to remember the keys by hard.
- **Export Integration**: Variables are part of the export functionality. Having well-defined classes ensures proper serialization and data exchange.

## Step 1: Create the Variable Class

Create a new Python file in the `cp/variables/` directory:

```python
# cp/variables/your_new_variable.py
from .variable import Variable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar


class YourNewVariable(Variable):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__()
        self._employees = employees
        self._days = days
        self._shifts = shifts

    def create(self, model: CpModel, variables: dict[str, IntVar]) -> list[IntVar]:
        created_vars = []

        for employee in self._employees:
            for day in self._days:
                # Binary variable (True/False)
                var = model.new_bool_var(
                    YourNewVariable.get_key(employee, day)
                )
                created_vars.append(var)

        return created_vars

    @staticmethod
    def get_key(employee: Employee, day: Day) -> str:
        return f"your_var_e:{employee.get_key()}_d:{day.strftime('%Y-%m-%d')}"
```

## Step 2: Export the Variable

Add your variable to the `__init__.py` files:

```python
# cp/variables/__init__.py
from .your_new_variable import YourNewVariable as YourNewVariable
```

```python
# cp/__init__.py
from .variables import (
    ...
    YourNewVariable as YourNewVariable
)
```

## Step 3: Register in solve.py

Add your variable to the main solver script:

```python
# solve.py
from cp import (
    # ... existing imports ...
    YourNewVariable,
)

def main():
    # ... existing code ...

    variables = [
        # ... existing variables ...
        YourNewVariable(employees, days, shifts),
    ]
```

## Variable Types

**Boolean Variables** (True/False decisions):
```python
var = model.new_bool_var(name)
```

**Integer Variables** (Numeric values):
```python
var = model.new_int_var(min_value, max_value, name)
```
