# General Structure

This document describes the overall structure and purpose of the components in this project.

## Core Entry Point

### `solving.py`
This is the **main script** for solving the scheduling problem.
It defines and initializes the model, adds constraints, and calls the solver.
All constraint logic is built up here by calling helper functions.

As solver we currently use the CP SAT Solver from Google's OR Tools.
> ! We do not know if this Solver is going to be suffient for all the
> differnt kinds of constraints. That is why it is important that we
> check the feasibility of all constraints as fast as possible. Alternative
> method we could explore is the use of gurobi.

---

## Constraint Modules

### `building_constraints/`
This folder contains the **implementation** of various constraint-building functions.

Each file defines a specific type of constraint:

- `initial_constraints.py`: basic structure like "one shift per employee per day"
- `free_shifts_and_vacation_days.py`: time-off and unavailability
- `target_working_hours.py`: enforces target working time with tolerance
- `minimal_number_of_staff.py`: (optional) under development

Note: These files **implement constraint logic**, not case-specific data.

---

## Output Handling

### `handlers.py`
Defines how the solution is **handled after solving**, including:

- Printing to console
- Saving to JSON
- Plotting (planned)

Currently, there's one unified handler class that supports **multiple output modes**, though not all are fully implemented yet (`print`, `plot`, `json`).

---

## Plotting (WIP)

### `plotting.py`
Contains functions for **visualizing the solution** (e.g., Gantt charts or shift tables).
This is **not yet fully implemented**, but planned to allow human-readable views of schedules.

---

## Global Program State

### `StateManager.py`
Contains a global `state` object used to store runtime-shared data.
Currently, it's used to track which constraints have been added.
Useful for handlers (e.g., saving metadata like applied constraints).

---

## Test Cases

### `cases/`
Holds different **example scenarios** (folders named by `case_id` like `1/`, `2/`, ...).
Each folder contains:

- Employee definitions
- Constraint settings
- Target working hours
- Time-off requests

This allows easy switching between different planning situations.

#### `case_catalog.md`
Markdown overview of all defined test cases, explaining their purpose and setup.

---

## Documentation

### `docs/`
Contains supporting documentation:

- `GeneralStructure.md`: this file
- `Constraints.md`: list of all constraints, one of the most important files
- `Images/`: optional folder for diagrams or screenshots

---

## Found Solutions

### `found_solutions/`
Automatically created folder to store output JSON files with solved schedules, based on the selected case and time of solving.

---

## Misc

- `.gitignore`: Standard Git ignore rules.
- `README.md`: Project overview and usage instructions.

---

## Summary

| Component         | Purpose                                           |
|------------------|---------------------------------------------------|
| `solving.py`      | Main entry point and problem setup               |
| `building_constraints/` | Logic for adding constraints to the model     |
| `handlers.py`     | Manages what happens with solutions              |
| `plotting.py`     | Planned human-readable schedule visualization    |
| `StateManager.py` | Stores global state like applied constraints     |
| `cases/`          | Real-world test scenarios with data              |
| `docs/`           | Markdown documentation and structure             |

---
