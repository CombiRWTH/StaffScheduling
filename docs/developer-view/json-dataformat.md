# JSON Data Formats

This page is the developer-oriented reference for JSON files used by the backend pipeline.
For user-editable configuration, prefer the User View configuration pages:

- [Overview of Configurations](../user-view/configuration/index.md)
- [Assemble Staff](../user-view/configuration/staff.md)
- [Modify Vacation Days](../user-view/configuration/vacation-days.md)
- [Modify Forbidden Days / Shifts](../user-view/configuration/forbidden-days.md)
- [Adapting Weights](../user-view/configuration/weights.md)
- [Modify Round Permissions](../user-view/configuration/rounds-permissions.md)
- [Qualification Mapping](../user-view/configuration/qualifications.md)
- [Minimal Number of Staff](../user-view/configuration/min-staff.md)
- [Blocking Shifts](../user-view/configuration/blocked-shifts.md)
- [Preplanning Shifts](../user-view/configuration/planned-shifts.md)
## File Location Convention

Most case files live in one of these locations:
- Month-based: `cases/{case_id}/{MM_YYYY}/{file}.json`
- Fallback: `cases/{case_id}/{file}.json`

The filesystem loader first uses the month folder if available.
---

## Shared Config Files (see User View)
The following files are documented in detail in the User View configuration pages and are only listed here for completeness:

- `employees.json`
- `employee_types.json`
- `free_shifts_and_vacation_days.json`
- `general_settings.json`
- `minimal_number_of_staff.json`
- `wishes_and_blocked.json`
- `weights.json` (optional, month-based; defaults are used if missing)

---
## Developer-Specific / Import Files

### File: `shift_information.json`
#### Description

Raw shift metadata exported from source systems. The solver currently uses internally defined shifts, but this file is still part of the case import data.

#### Structure

```jsonc
[
  {
    "break_duration": "float",                 // Minutes
    "end_time": "string YYYY-MM-DDTHH:MM:SS",
    "shift_duration": "float",                 // Minutes (including break)
    "shift_id": "string",
    "shift_name": "string",
    "start_time": "string YYYY-MM-DDTHH:MM:SS",
    "working_minutes": "float"                 // Minutes (excluding break)
  }
]
```
### File: `target_working_minutes.json`

#### Description

Target and already recorded working minutes per employee for the planning month.

#### Structure

```jsonc
{
  "employees": [
    {
      "key": "int",
      "firstname": "string",
      "name": "string",
      "actual": "float",   // Already recorded minutes
      "target": "float"    // Monthly target minutes
    }
  ]
}
```
### File: `worked_sundays.json`

#### Description

Historical helper data for Sundays worked in the last 12 months.

#### Structure

```jsonc
{
  "worked_sundays": [
    {
      "key": "int",
      "firstname": "string",
      "name": "string",
      "worked_sundays": "int"
    }
  ]
}
```
---
