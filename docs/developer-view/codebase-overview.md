# Project Structure

## Source Code (`src/`)

The main source code is organized in the `src/` directory:

## Core Data Models


```
src/
├── main.py                  # Main entry point
├── solve.py                 # Most important class to combine everything for the solver. Command-line solver interface.
└── plot.py                  # Visualization utilities
```

Additianal there are the following helper classes:
```
src/
├── employee.py
├── day.py
├── shift.py
└── solution.py
```

## Constraint Programming Engine (`src/cp/`)

The core of the optimization system, is build in the **cp** directory:

```
src/cp/
├── __init__.py                # CP module exports
├── model.py                   # Main optimization model
├── variables/                 # Decision variables
│   ├── variable.py           # Base variable class
│   ├── employee_day.py       # Employee-day assignments
│   └── employee_day_shift.py # Employee-day-shift assignments
├── constraints/               # Business rules and restrictions
│   ├── constraint.py         # Base constraint class
│   ├── max_one_shift_per_day.py
│   ├── min_staffing.py
│   ├── target_working_time.py
│   └── ...                   # Various constraint implementations
└── objectives/                # Optimization goals
    ├── objective.py          # Base objective class
    ├── minimize_overtime.py
    ├── maximize_wishes.py
    └── ...                   # Various objective implementations
```

**Key Components:**

- **Variables**: Define variables used for objectives and constraints
- **Constraints**: Define what rules must be followed
- **Objectives**: Define what outcomes to optimize for
- **Model**: Orchestrates the entire optimization process

## Data Loading (`src/loader/`)

Handles different data input formats:

```
src/loader/
├── loader.py                 # Is used an an interface to access the methods in filesystem_loader.py
└── filesystem_loader.py      # JSON/file-based data loading usd for loading the files from the drive
```

## Database Integration (`src/db/`)

Database connectivity and data persistence:

```
src/db/
├── connection_setup.py      # Database connection configuration
├── export_data.py           # Export data to database
├── export_main.py           # Main export functionality
├── import_main.py           # Main import functionality
└── import_solution.py       # Import scheduling solutions
```

## Web Interface (`src/web/`)

Web-based user interface:

```
src/web/
├── app.py                   # Flask web application
├── analyze_solution.py
└── templates/
    └── index.html           # Main web interface template
```

## Test Cases (`cases/`)

Sample data and test scenarios:

```
cases/
├── 1/
│   ├── employees.json
│   ├── general_settings.json
│   └── ...
├── 2/
├── 3/
└── case_catalog.md         # Documentation of test cases
```
## Documentation (`docs/`)

The files for this documentation. ;)
