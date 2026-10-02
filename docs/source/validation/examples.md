# Examples and reproduction

For readers trying to inspect or reproduce the example schedules. The prepared TimeOffice inputs below exist; how they were checked is recorded under [current limitations](index.md#webapp-integration). The bundle format, the TimeOffice-free commands and the validator below are implemented and tested; the accepted six-month example files are not yet part of the repository.

Return to the [documentation overview](../index.md).

## Example scope and file inventory

Two fictional stations and one jumper pool, planned together for each month from January to June 2026: twelve station months. Station `BSP-A` uses demand profile 85 and `BSP-B` profile 79 of the chair's minimum-staffing table; the profile numbers are labels, not database keys. The TimeOffice units and their keys are listed in the [adapter reference](../architecture/timeoffice.md#prepared-example-units). Exported files are not yet part of the repository.

## Input data and boundary context

All people, contracts and absences are invented for the example, all of them adults. Names follow the pattern `Beispiel A Anna` (surname = home unit) and staff numbers `BSP-A-P01` (P professional, H assistant, AZ trainee, MFA medical assistant).

| Home unit  | Professional | Assistant | Trainee | MFA |
| ---------- | ------------ | --------- | ------- | --- |
| `BSP-A`    | 9            | 4         | 6       | 3   |
| `BSP-B`    | 13           | 6         | 6       | 3   |
| `BSP-JUMP` | 5            | 2         | –       | –   |

- **Contracts.** Full time is 39 hours a week; some staff work 29.25 or 19.5 hours. The monthly target is the weekly hours ÷ 5 for each Monday–Friday that is not an NRW public holiday. Holiday-rich months therefore have lower targets but the same demand.
- **Eligibility.** Station staff are members of their station only. Jumper pool staff have the jumper pool as home and replacement memberships at both stations. Memberships run from 2025-12-01 to 2026-07-31, which covers the boundary context.
- **Absences.** Everyone has three five-workday vacation blocks (`U`) spread over the half year. Each trainee also has one school week (`SC`) per month outside their vacation. Each absence workday is credited with the weekly hours ÷ 5 in TimeOffice's daily accounts.
- **Demand.** Saved per station month from the profile's weekday and weekend/holiday rows (NRW holidays take the weekend row). Professional, assistant, trainee and MFA demand stay separate.
- **Capacity.** Per qualification and month, target minus credits exceeds demand hours by 4–60 % (May is tightest: assistants 1.04, professionals 1.07). This is an hours check only; it does not show that a schedule satisfying every rule exists.
- **Boundary context.** Fictional worked duties for 2025-12-18 to 2025-12-31 and 2026-07-01 to 2026-07-07 respect one duty per day, no early shift after a late shift, no day shift directly after a night, at most three nights in a row followed by two free days, and at most five consecutive working days; the shortest rest between duties is 14 hours. They meet the stations' demand on every context day. These properties were checked on the duties read back from the database, separately from the code that produced them. Generation reads this context as trusted duties around the month. Three professionals' July 3 nights were removed afterwards, because with them no professional could work the June 30 night within the night and recovery rules.
- **Not included.** Wishes, special capabilities and history before 2025-12-18. Annual free Sundays need the whole year and cannot be assessed from this data.

## Bundle files

A monthly bundle is one folder `YYYY-MM/` with four files, produced by **Prüfen** downloads or `solve` below. JSON is the complete reproduction format; the CSV tables are the readable submission format and are derived from the JSON pair, never read back.

| File            | Content                                                                                                                                                                                                                                                                                                                                                                              |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `input.json`    | `format_version` (1), `timezone` (`Europe/Berlin`), the month's `calendar` (date, ISO weekday Monday=1, NRW public holiday name) and the canonical `dataset`: stations and jumper pools, shifts with work segments and paid minutes, dated demand, employees, dated memberships, binding availability, monthly accounts with dated credits and the trusted context with its coverage |
| `result.json`   | `format_version`, `planning_month`, `input` (`file` and hex `sha256` of the exact `input.json` bytes), the `solution` (CP-SAT status, effective configuration with rule policy, weights, timeout, workers and seed, wall time, assignments, objective value and bound, diagnostics and the independent `check`) and the solving `versions` of Python, OR-Tools and Pydantic          |
| `schedule.csv`  | One row per duty, sorted by date, station, start and employee                                                                                                                                                                                                                                                                                                                        |
| `employees.csv` | One row per participating employee, also without duties, sorted by ID                                                                                                                                                                                                                                                                                                                |

The JSON Schemas are generated from the Pydantic models: [input.schema.json](schema/input.schema.json) and [result.schema.json](schema/result.schema.json). Parsing rejects unknown fields, other format versions and a calendar that is not the month's NRW calendar. Derived values (month start/end, credited totals, the relative gap, health events) are left out of the files and recomputed. There is no wish field and no TimeOffice plan, credential or SQL row; IDs are the canonical positive numbers.

`schedule.csv` columns: `employee_id`, `employee_name`, `date`, `weekday`, `is_public_holiday`, `planning_unit_id` and `planning_unit_name` (the station where the duty is worked), `shift_id`, `shift_code`, `shift_type`, `start_at` and `end_at` (ISO 8601 with Europe/Berlin offset; a night ends on the next date and a duty belongs to its start date), `net_work_minutes` (paid), `staff_level` (the credited qualification), and `origin_unit_id`, `origin_unit_name`, `origin_unit_type` (the employee's home station or jumper pool on that date).

`employees.csv` columns: `employee_id`, `employee_name`, `staff_level` (employee level), `planning_month` (`YYYY-MM`), `target_minutes`, `credited_minutes`, `generated_minutes`, `balance_minutes` (generated + credited − target), and `memberships`, `hard_availability`, `credit_details`: complete JSON arrays copied from the input, in quoted cells.

CSV conventions: UTF-8, comma, one header row, standard-library quoting, `\n` line ends, `true`/`false` booleans, integer minutes, full ISO dates. An empty cell only appears in the origin columns, for a duty of an employee without membership that day, which the check reports as an eligibility finding.

## Run without TimeOffice

From `api/`, with the [native tools](../getting-started/installation.md#optional-native-developer-setup) installed:

```sh
uv run --frozen python -m app.solver.examples solve ../examples/2026-01 --timeout 120
```

`solve` reads `input.json` of the folder, solves it with the [solver settings](../getting-started/installation.md) (`--timeout` overrides `SOLVER_MAX_TIME_SECONDS`) and writes `result.json`, `schedule.csv` and `employees.csv` beside it. Without a found schedule it writes nothing, prints the diagnostics and exits with status 1. A rerun can find another equally valid schedule; byte-identical results are not expected.

An input for a month comes from **Prüfen** after a generation (`input.json`) or from `GET /review/files/input.json`. Each month's input carries its own trusted context; supplying the preceding accepted month as context is part of preparing the sequence, not done by `solve`.

To regenerate the published schemas after a model change:

```sh
uv run --frozen python -m app.solver.examples schema ../docs/source/validation/schema
```

A test fails while the committed schemas differ from the models.

## Validate monthly and sequence results

```sh
uv run --frozen python -m app.solver.examples check ../examples --first 2026-01 --last 2026-06
```

The command prints one summary line per month and `PASS` or every problem with `FAIL`, and exits with status 1 on any problem. It accepts the folders only if:

- exactly the months from first to last are present as `YYYY-MM` folders, each with four nonempty files, all planning the same stations and jumper pools;
- every pair is a valid bundle as for an import (format, digest, month, references, found schedule, current rule settings, stored check equal to a re-check);
- `result.json`, `schedule.csv` and `employees.csv` equal the canonical rendering of the pair, so the tables contain exactly the canonical duties and every participant's account, memberships, availability and credits;
- the check is **accepted**: no finding and no blocking gap. Rejected or incomplete results are reported as _diagnostic result, not an example_;
- every duty has an evidenced origin;
- consecutive months agree: the trusted context duties of a month on the other month's dates equal that month's schedule (both directions), and the availability of the first date of the later month equals the earlier month's context availability.

Non-blocking open items stay visible in the summary: the following month's start (checked by the next month with this schedule as context) and annual free Sundays, which need the whole year and are never reported as passed.

## Interpret objectives and solver settings

The check's `scores` are the three tiers of the objective, highest first: health events (`six_day_windows` + `backward_transitions`), `balance_deviation_minutes` (sum of absolute account balances) and `surplus_intermediate_duties`. `configuration.weights` are the dominance coefficients derived from the input, so one unit of a higher tier outweighs any change of the lower ones; `objective.value` equals the weighted total of the recomputed scores and `best_bound` is CP-SAT's proven bound. A time-limited `feasible` run can be improved by up to the gap. `configuration.policy` records every rule parameter; see the [solver reference](../architecture/solver.md).
