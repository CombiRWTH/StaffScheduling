# Adding a New Variable to the Shift Scheduling System

This guide explains how to create and integrate a new variable into the shift scheduling system.

## Overview

Variables are the decision elements that the solver can set when creating a schedule. They represent choices like "Does employee X work shift Y on day Z?"

## Why Variable Classes?
- **Consistent Referencing**: Variables are used in multiple constraints and objectives. Having dedicated classes makes it easier to reference them consistently instead of needing to remember the keys.
- **Export Integration**: Variables are part of the export functionality. Having well-defined classes ensures proper serialization and data exchange.

## Step 1: Create the Variable Class

Create a new variable in `cp/variables/variable.py`:

```python
# cp/variables/your_new_variable.py

# an example template, which you could follow
class YourNewVariable:
    """
 A dictionary wrapper that allows indexing with different objects (e.g., Employee, Day, and Shift).

 Usage: wrapper_dict[...]...[...] -> Variable
 """

    def __init__(self, internal_dict: dict[key, value]):
        self._data = internal_dict

    def __getitem__(self, key) -> value:
        return self._data[employee.get_key()]

    def __len__(self) -> int:
 l = ...
        # compute length
        return l

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

## CP-SAT Variable Types

**Boolean Variables** (True/False decisions):
```python
var = model.new_bool_var(name)
```

**Integer Variables** (Numeric values):
```python
var = model.new_int_var(min_value, max_value, name)
```
