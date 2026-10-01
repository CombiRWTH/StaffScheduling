# Underlying Data Structures

> This page describes the imported UI and its legacy file model. Views remain present during migration; API generation, progress, publication and shared-file assumptions have known gaps. See [integration limits](solver-integration.md). Screenshots depict the imported UI, not verified end-to-end behavior.


This reference documents all JSON files used by the StaffScheduling system. Files are stored on disk
and accessed by both the web application (via LowDB) and the Python solver. Understanding these
structures is essential when debugging, migrating data, or contributing to the codebase.

---

## File System Layout

```
cases/
└── <caseId>/                          # e.g. 77
    ├── templates/                     # Case-level templates (not month-specific)
    │   ├── global-wishes.json
    │   ├── minimal-staff.json
    │   └── weights.json
    └── <monthYear>/                   # e.g. 11_2024
        ├── employees.json             # ← Solver writes, Web reads
        ├── employee_types.json        # ← Solver writes, Web reads
        ├── wishes_and_blocked.json    # ← Web writes, Solver reads
        ├── global_wishes_and_blocked.json  # ← Web writes only
        ├── minimal_number_of_staff.json    # ← Web writes, Solver reads
        ├── weights.json               # ← Web writes, Solver reads
        ├── general_settings.json      # ← Solver writes, Web reads
        ├── shift_information.json     # ← Solver writes, Web reads
        ├── target_working_minutes.json     # ← Solver writes, Web reads
        ├── free_shifts_and_vacation_days.json  # ← Solver writes, Web reads
        ├── worked_sundays.json        # ← Solver writes, Web reads
        └── web/                       # Written exclusively by the web application
            ├── jobs.json
            ├── schedules.json
            ├── schedule_<id>.json     # One file per imported schedule
            └── last_inserted.json     # Tracks the last inserted solution
```

The `caseId` is a numeric identifier matching the TimeOffice planning unit number. The `monthYear`
directory uses the format `MM_YYYY` (e.g. `11_2024` for November 2024).

## Data Ownership Matrix

The following table clarifies which system writes and reads each file. This is critical for
understanding which files are safe to edit manually and which will be overwritten.

| File | Written by | Read by | Safe to edit manually? |
|---|---|---|---|
| `employees.json` | Solver (fetch) | Web | No — re-fetch overwrites |
| `employee_types.json` | Solver (fetch) | Web, Solver | Yes (static template) |
| `shift_information.json` | Solver (fetch) | Web | No — re-fetch overwrites |
| `general_settings.json` | Solver (fetch) | Solver | Yes (static template) |
| `target_working_minutes.json` | Solver (fetch) | Solver | No — re-fetch overwrites |
| `free_shifts_and_vacation_days.json` | Solver (fetch) | Solver | No — re-fetch overwrites |
| `worked_sundays.json` | Solver (fetch) | Solver | No — re-fetch overwrites |
| `wishes_and_blocked.json` | Web | Solver | Yes — but global wishes may overwrite |
| `global_wishes_and_blocked.json` | Web | Web | Yes |
| `minimal_number_of_staff.json` | Web | Solver | Yes |
| `weights.json` | Web | Solver | Yes |
| `web/jobs.json` | Web | Web | Not recommended |
| `web/schedules.json` | Web | Web | Not recommended |
| `web/schedule_<id>.json` | Web | Web | Not recommended |
| `web/last_inserted.json` | Web | Web | Not recommended |

---

## Solver-Side Files

These files are created and updated by the StaffScheduling Python project (via the `fetch`
operation). The web application reads them but does not write to them directly.

### employees.json

A flat list of employees belonging to the ward.

```json
{
  "employees": [
    {
      "key": 459,
      "name": "Shoemake",
      "firstname": "Sandra",
      "type": "Krankenschwester/-pfleger (81302-008)"
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `key` | `number` | Unique employee identifier from TimeOffice |
| `name` | `string` | Family name |
| `firstname` | `string` | First name |
| `type` | `string` | Full role type string from TimeOffice (see `employee_types.json`) |

### employee_types.json

Maps the raw `type` strings from `employees.json` to one of three solver categories:
**Fachkraft** (skilled professional), **Hilfskraft** (support worker), **Azubi** (trainee).

```json
{
  "Azubi": [
    "A-Gesundheits- und Krankenpfleger/in (A-81302-005)"
  ],
  "Fachkraft": [
    "Altenpfleger/in (82102-002)",
    "Krankenschwester/-pfleger (81302-008)"
  ],
  "Hilfskraft": [
    "Pflegeassistenz (81317-003)"
  ]
}
```

| Key | Solver category | Description |
|---|---|---|
| `Fachkraft` | Skilled | Determines minimum staffing for the skilled-staff rows in `minimal_number_of_staff.json` |
| `Hilfskraft` | Support | Determines minimum staffing for the support rows |
| `Azubi` | Trainee | Determines minimum staffing for the trainee rows |

> **Note:** If a new employee type appears in TimeOffice that is not listed in any of the three
> categories, the solver will not be able to classify that employee. In this case, you must
> manually add the new type string to the appropriate category in this file.

### shift_information.json

An array of shift definitions fetched from TimeOffice. The solver uses these to identify which
shift IDs correspond to Early (F), Late (S), and Night (N) shifts.

```json
[
  {
    "shift_id": "2939",
    "start_time": "2000-01-01T06:00:00",
    "end_time": "2000-01-01T14:10:00",
    "working_minutes": 460.0,
    "break_duration": 30.0,
    "shift_duration": 490.0,
    "shift_name": "F2_"
  }
]
```

| Field | Type | Description |
|---|---|---|
| `shift_id` | `string` | TimeOffice shift identifier |
| `start_time` | `string` | ISO datetime (date part is always `2000-01-01`, only time is relevant) |
| `end_time` | `string` | ISO datetime |
| `working_minutes` | `number` | Net working time in minutes (excluding breaks) |
| `break_duration` | `number` | Break time in minutes |
| `shift_duration` | `number` | Total shift duration in minutes |
| `shift_name` | `string` | Human-readable label from TimeOffice |

**Standard shift types recognized by the solver:**

| Abbreviation | Internal ID | Name | German |
|---|---|---|---|
| F | 0 | Early | Frühschicht |
| Z | 1 | Intermediate | Zwischenschicht |
| S | 2 | Late | Spätschicht |
| N | 3 | Night | Nachtschicht |
| Z60 | 4 | Management | Leitungsschicht |

### general_settings.json

Maps the three solver shift identifiers (Early, Late, Night) to their internal index values,
and stores any special per-employee qualifications.

```json
{
  "SHIFT_NAME_TO_INDEX": {
    "Early": 0,
    "Late": 1,
    "Night": 2
  },
  "qualifications": {
    "791": ["rounds"]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `SHIFT_NAME_TO_INDEX` | `Record<string, number>` | Maps canonical shift names to indices (always 0/1/2) |
| `qualifications` | `Record<string, string[]>` | Employee key → list of special qualifications (e.g. `"rounds"` for round-eligible employees) |

### target_working_minutes.json

The monthly working time target and current actual (accumulated) total for each employee.

```json
{
  "employees": [
    {
      "key": 459,
      "name": "Shoemake",
      "firstname": "Sandra",
      "target": 7680.0,
      "actual": 0.0
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `key` | `number` | Employee identifier |
| `target` | `number` | Monthly target working minutes |
| `actual` | `number` | Actual worked minutes so far (0 before scheduling, updated after insertion) |

### free_shifts_and_vacation_days.json

Pre-planned absences and pre-assigned shifts fetched from TimeOffice. The solver uses this as
hard constraints: employees cannot be scheduled on their `vacation_days` or `forbidden_days`.

```json
{
  "employees": [
    {
      "key": 459,
      "name": "Shoemake",
      "firstname": "Sandra",
      "vacation_days": [12],
      "forbidden_days": [18, 22, 23, 24, 25],
      "planned_shifts": []
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `vacation_days` | `number[]` | Calendar days (1–31) the employee has approved leave |
| `forbidden_days` | `number[]` | Calendar days the employee may not work (public holidays, prior commitments) |
| `planned_shifts` | `array` | Pre-assigned shifts that must be kept in the schedule |

### worked_sundays.json

Historical count of Sundays worked by each employee. The solver uses this to fairly distribute
Sunday assignments across the team.

```json
{
  "worked_sundays": [
    {
      "key": 927,
      "name": "Mittrach",
      "firstname": "Margaritt",
      "worked_sundays": 2
    }
  ]
}
```

---

## Web-Application Files

These files are created and maintained exclusively by the Next.js web application.

### wishes_and_blocked.json

Stores monthly (date-specific) employee preferences entered via the Wishes & Blocked page.

```json
{
  "employees": [
    {
      "key": 914,
      "firstname": "Silvia",
      "name": "Harkins",
      "wish_days": [],
      "wish_shifts": [[5, "S"]],
      "blocked_days": [1, 8],
      "blocked_shifts": []
    }
  ]
}
```

| Field | Type | Constraint strength | Description |
|---|---|---|---|
| `wish_days` | `number[]` | Soft | Calendar days (1–31) the employee prefers to have off |
| `wish_shifts` | `[number, "F"\|"S"\|"N"][]` | Soft | Preferred shifts: `[day, shiftCode]` |
| `blocked_days` | `number[]` | Hard | Calendar days the employee must not work |
| `blocked_shifts` | `[number, "F"\|"S"\|"N"][]` | Hard | Shifts the employee must not be assigned |

Day numbers are **calendar days** within the selected month (1–31).

### global_wishes_and_blocked.json

Stores recurring weekly preferences entered via the Global Wishes & Blocked page.
The structure is identical to `wishes_and_blocked.json`, but day numbers refer to **weekday
indices** rather than calendar dates.

```json
{
  "employees": [
    {
      "key": 791,
      "wish_days": [],
      "wish_shifts": [[3, "S"]],
      "blocked_days": [],
      "blocked_shifts": []
    }
  ]
}
```

**Weekday index mapping:**

| Index | Weekday |
|---|---|
| 1 | Monday |
| 2 | Tuesday |
| 3 | Wednesday |
| 4 | Thursday |
| 5 | Friday |
| 6 | Saturday |
| 7 | Sunday |

When a global wish is saved for an employee, the system regenerates all corresponding monthly
entries in `wishes_and_blocked.json` (replacing any prior monthly entries for that employee).

### minimal_number_of_staff.json

Defines the minimum number of employees per staffing category, per shift, per weekday. The solver
enforces these as hard constraints.

```json
{
  "Azubi": {
    "Mo": { "F": 0, "S": 0, "N": 0 },
    "Di": { "F": 0, "S": 0, "N": 0 },
    "Mi": { "F": 0, "S": 0, "N": 0 },
    "Do": { "F": 0, "S": 0, "N": 0 },
    "Fr": { "F": 0, "S": 0, "N": 0 },
    "Sa": { "F": 0, "S": 0, "N": 0 },
    "So": { "F": 0, "S": 0, "N": 0 }
  },
  "Fachkraft": {
    "Mo": { "F": 2, "S": 2, "N": 1 }
  },
  "Hilfskraft": {
    "Mo": { "F": 1, "S": 1, "N": 0 }
  }
}
```

Top-level keys correspond to the three solver categories (`Azubi`, `Fachkraft`, `Hilfskraft`).

Weekday keys: `Mo`, `Di`, `Mi`, `Do`, `Fr`, `Sa`, `So`.

Shift keys: `F` (Early), `S` (Late), `N` (Night).

### weights.json

Penalty weights for soft constraints. Higher values make the solver more aggressively avoid
a given pattern. These weights only apply when running the **`solve`** command (single schedule
generation). `solve-multiple` ignores this file and uses three internal presets
(see [Solver Integration — Weight Presets](../collection-of-old-docs/webapp/solver-integration.md#weight-presets)).

```json
{
  "free_weekend": 2,
  "consecutive_nights": 2,
  "hidden": 100,
  "overtime": 4,
  "consecutive_days": 1,
  "rotate": 1,
  "wishes": 15,
  "after_night": 3,
  "second_weekend": 1
}
```

| Field | Description |
|---|---|
| `free_weekend` | Penalty for not giving an employee at least one free weekend |
| `consecutive_nights` | Penalty for more than three consecutive night shifts |
| `hidden` | Internal penalty reserved for hard-coded solver constraints (hidden employees) |
| `overtime` | Penalty per overtime hour |
| `consecutive_days` | Penalty for more than five consecutive working days |
| `rotate` | Penalty for violating the forward rotation rule (F → S → N) |
| `wishes` | Penalty per unfulfilled soft wish |
| `after_night` | Penalty for not granting a free day after a night shift |
| `second_weekend` | Penalty for scheduling an employee on a second full weekend in a month |

---

## Web-Managed Output Files (`web/`)

The `web/` subdirectory is entirely managed by the Next.js application.

### web/jobs.json

A log of all solver operations triggered via the web interface.

```json
{
  "jobs": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "solve",
      "status": "completed",
      "caseId": 77,
      "params": {
        "unit": 77,
        "start": "2024-11-01",
        "end": "2024-11-30",
        "timeout": 5
      },
      "consoleOutput": "...",
      "createdAt": "2024-11-15T10:00:00.000Z",
      "completedAt": "2024-11-15T10:05:00.000Z",
      "duration": 20660,
      "metadata": {
        "solutionsGenerated": 1,
        "expectedSolutions": 1
      }
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | `string` | UUID assigned by the web application |
| `type` | `"fetch" \| "solve" \| "solve-multiple" \| "insert" \| "delete"` | Operation type |
| `status` | `"pending" \| "running" \| "completed" \| "failed"` | Job lifecycle state |
| `params.timeout` | `number` | Solver timeout in minutes |
| `duration` | `number` | Wall-clock execution time in milliseconds |
| `metadata.solutionsGenerated` | `number` | Number of schedules produced |

### web/schedules.json

Metadata and quality statistics for all schedules imported into this case.

```json
{
  "schedules": [
    {
      "scheduleId": "imported_wdefault_2026-03-08T14-24-35-337Z",
      "description": "Variant A",
      "generatedAt": "2026-03-08T14:24:35.337Z",
      "isSelected": false,
      "stats": {
        "forward_rotation_violations": 68,
        "consecutive_working_days_gt_5": 9,
        "no_free_weekend": 33,
        "consecutive_night_shifts_gt_3": 5,
        "total_overtime_hours": 376,
        "no_free_days_around_weekend": 109,
        "not_free_after_night_shift": 20,
        "violated_wish_total": 1
      }
    }
  ]
}
```

| Field | Description |
|---|---|
| `scheduleId` | Must match the filename `web/schedule_<scheduleId>.json` |
| `isSelected` | When `true`, this schedule is used for the Insert operation |
| `stats.forward_rotation_violations` | Count of F→S→N rule violations |
| `stats.consecutive_working_days_gt_5` | Count of runs exceeding 5 consecutive working days |
| `stats.no_free_weekend` | Count of employees with no free weekend in the month |
| `stats.consecutive_night_shifts_gt_3` | Count of night-shift runs exceeding 3 consecutive nights |
| `stats.total_overtime_hours` | Sum of overtime hours across all employees |
| `stats.no_free_days_around_weekend` | Count of missed free days adjacent to weekends |
| `stats.not_free_after_night_shift` | Count of night shifts not followed by a free day |
| `stats.violated_wish_total` | Total number of soft wishes that could not be satisfied |

### web/schedule_&lt;id&gt;.json

One file per imported or generated schedule. Contains the full shift assignment matrix as
produced by the Python solver. The file name must match the `scheduleId` field in
`web/schedules.json`.

The structure follows the solver's processed solution format:

```json
{
  "variables": {
    "(459, '2024-11-01', 0)": 1,
    "(459, '2024-11-02', 2)": 1
  },
  "employees": [
    {
      "id": 459,
      "name": "Shoemake Sandra",
      "level": "Fachkraft",
      "target_working_time": 7680,
      "actual_working_time": 1920,
      "wishes": {
        "shift_wishes": [[25, "F"]],
        "day_off_wishes": [18, 22, 23]
      },
      "forbidden_days": [18, 22, 23, 24, 25],
      "vacation_days": [2, 3, 4, 5]
    }
  ],
  "days": ["2024-11-01", "2024-11-02"],
  "shifts": [
    {
      "id": 0,
      "name": "Früh",
      "abbreviation": "F",
      "color": "#a8d51f",
      "duration": 460,
      "is_exclusive": false
    }
  ],
  "stats": {
    "forward_rotation_violations": 5,
    "consecutive_working_days_gt_5": 2,
    "no_free_weekend": 1,
    "consecutive_night_shifts_gt_3": 0,
    "total_overtime_hours": 12.5,
    "no_free_days_around_weekend": 3,
    "not_free_after_night_shift": 1,
    "violated_wish_total": 8
  },
  "fulfilled_shift_wish_cells": [[459, "2024-11-15"]],
  "fulfilled_day_off_cells": [[459, "2024-11-18"]],
  "all_shift_wish_colors": {
    "459-2024-11-15": ["#a8d51f"]
  },
  "all_day_off_wish_cells": [[459, "2024-11-18"]]
}
```

| Field | Type | Description |
|---|---|---|
| `variables` | `Record<string, 0\|1>` | Shift assignment matrix. Key format: `(employee_key, 'YYYY-MM-DD', shift_id)` |
| `employees` | `array` | Employee data with wishes, vacation, and working time information |
| `days` | `string[]` | All dates in the scheduling period (`YYYY-MM-DD`) |
| `shifts` | `array` | Shift definitions with display colors for the UI |
| `stats` | `object` | Quality metrics (same structure as in `schedules.json`) |
| `fulfilled_shift_wish_cells` | `[number, string][]` | `[employee_id, date]` pairs where shift wishes were honored |
| `fulfilled_day_off_cells` | `[number, string][]` | `[employee_id, date]` pairs where day-off wishes were honored |
| `all_shift_wish_colors` | `Record<string, string[]>` | Map of `"employee_id-date"` → shift colors (for UI visualization) |
| `all_day_off_wish_cells` | `[number, string][]` | All cells where a day-off wish existed (fulfilled or not) |

### web/last_inserted.json

Tracks the last schedule that was inserted into TimeOffice via the Insert operation. This allows
the Delete operation to know which schedule to remove.

```json
{
  "scheduleId": "imported_wdefault_2026-03-08T14-24-35-337Z",
  "insertedAt": "2026-03-08T15:00:00.000Z"
}
```

| Field | Type | Description |
|---|---|---|
| `scheduleId` | `string` | ID of the schedule that was inserted |
| `insertedAt` | `string` | ISO timestamp of the insertion |

This file is created by the Insert operation and cleared by the Delete operation.

---

## Template Files

Templates are stored at the case level (`cases/<caseId>/templates/`) and are independent of
any specific month. They allow saving and loading configurations across different months.

### templates/weights.json

```json
{
  "templates": [
    {
      "content": {
        "free_weekend": 2,
        "consecutive_nights": 2,
        "hidden": 100,
        "overtime": 4,
        "consecutive_days": 1,
        "rotate": 1,
        "wishes": 15,
        "after_night": 3,
        "second_weekend": 1
      },
      "_metadata": {
        "id": "1773337370231",
        "description": "default",
        "last_modified": "2026-03-12T17:42:50.231Z"
      }
    }
  ]
}
```

The `content` object is identical in structure to `weights.json` described above.

### templates/minimal-staff.json

```json
{
  "templates": [
    {
      "content": { },
      "_metadata": {
        "id": "...",
        "description": "default",
        "last_modified": "..."
      }
    }
  ]
}
```

The `content` object is identical in structure to `minimal_number_of_staff.json`.

### templates/global-wishes.json

```json
{
  "templates": [
    {
      "content": {
        "employees": [ ]
      },
      "_metadata": {
        "id": "...",
        "description": "Test",
        "last_modified": "...",
        "employeeCount": 2,
        "employeeIds": [791, 459]
      }
    }
  ]
}
```

The `content.employees` array is identical in structure to the `employees` array in
`global_wishes_and_blocked.json`. The `_metadata` object additionally stores `employeeCount`
and `employeeIds` to allow the UI to warn if the loaded template contains employees that do
not exist in the currently selected case.
