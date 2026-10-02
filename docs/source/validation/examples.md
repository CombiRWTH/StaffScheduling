# Examples and reproduction

For readers trying to inspect or reproduce the example schedules. The prepared TimeOffice inputs below exist; how they were checked is recorded under [current limitations](index.md#webapp-integration). The bundle format, the TimeOffice-free tests and the validator below are implemented and tested; the accepted six-month example files are not yet part of the repository.

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
- **Wishes.** 38 fictional wishes, two per unit and month (`BSP-A`, `BSP-B`, `BSP-JUMP`) plus one more in January (`BSP-A`) and April (`BSP-JUMP`), covering free days, free shifts, preferred days and preferred shifts; two of them (`Beispiel A Anna` on 2026-01-05, `Beispiel Springer Frieda` on 2026-04-27) fall on the employee's own vacation and are not grantable by design.
- **Not included.** Special capabilities, replacement memberships of station staff and history before 2025-12-18. Annual free Sundays need the whole year and cannot be assessed from this data.

## Bundle files

A monthly bundle is one folder `YYYY-MM/` with five files, as downloaded from **Prüfen**. JSON is the complete reproduction format; the CSV tables are the readable submission format and are derived from the JSON pair, never read back.

| File            | Content                                                                                                                                                                                                                                                                                                                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `input.json`    | `format_version` (2), `timezone` (`Europe/Berlin`), the month's `calendar` (date, ISO weekday Monday=1, NRW public holiday name) and the canonical `dataset`: stations and jumper pools, shifts with work segments and paid minutes, dated demand, employees, dated memberships, binding availability, wishes, monthly accounts with dated credits and the trusted context with its coverage                                          |
| `result.json`   | `format_version`, `planning_month`, `input` (`file` and hex `sha256` of the exact `input.json` bytes), the `solution` (CP-SAT status, effective configuration with rule policy, total timeout, workers and seed, wall time, assignments, gaps, every objective stage with value, status and bound, diagnostics and the independent `check` with scores and wish outcomes) and the solving `versions` of Python, OR-Tools and Pydantic |
| `schedule.csv`  | One row per duty, sorted by date, station, start and employee                                                                                                                                                                                                                                                                                                                                                                         |
| `employees.csv` | One row per participating employee, also without duties, sorted by ID                                                                                                                                                                                                                                                                                                                                                                 |
| `gaps.csv`      | One row per station, date, shift and qualification with unfilled required slots, sorted by station, date, shift and qualification; only the header when there are none                                                                                                                                                                                                                                                                |

The JSON Schemas are generated from the Pydantic models: [input.schema.json](schema/input.schema.json) and [result.schema.json](schema/result.schema.json). Parsing rejects unknown fields, other format versions and a calendar that is not the month's NRW calendar. Derived values (month start/end, credited totals, health events, wish counts) are left out of the files and recomputed. There is no TimeOffice plan, credential or SQL row; IDs are the canonical positive numbers.

`schedule.csv` columns: `employee_id`, `employee_name`, `date`, `weekday`, `is_public_holiday`, `planning_unit_id` and `planning_unit_name` (the station where the duty is worked), `shift_id`, `shift_code`, `shift_type`, `start_at` and `end_at` (ISO 8601 with Europe/Berlin offset; a night ends on the next date and a duty belongs to its start date), `net_work_minutes` (paid), `staff_level` (the credited qualification), and `origin_unit_id`, `origin_unit_name`, `origin_unit_type` (the employee's home station or jumper pool on that date).

`employees.csv` columns: `employee_id`, `employee_name`, `staff_level` (employee level), `planning_month` (`YYYY-MM`), `target_minutes`, `credited_minutes`, `generated_minutes`, `balance_minutes` (generated + credited − target), and `memberships`, `hard_availability`, `credit_details`: complete JSON arrays copied from the input, in quoted cells.

`gaps.csv` columns: `planning_unit_id`, `planning_unit_name`, `date`, `shift_id`, `shift_code`, `staff_level`, `required_count`, `assigned_count` and `missing_count` (required − assigned). Gaps are never duties; they name the slots for which guest staff is needed.

Wish outcomes stay in `result.json` (`solution.check.wishes`, each wish with `status` `granted`, `denied` or `not_grantable`); they are not a CSV table.

CSV conventions: UTF-8, comma, one header row, standard-library quoting, `\n` line ends, `true`/`false` booleans, integer minutes, full ISO dates. An empty cell only appears in the origin columns, for a duty of an employee without membership that day, which the check reports as an eligibility finding.

## Reproduce without TimeOffice

From the repository root, with the [native tools](../getting-started/installation.md#optional-native-developer-setup) installed:

```sh
just test -m reproduction tests/test_examples.py
```

The reproduction tests solve every committed `input.json` again with the time limit, search workers and seed recorded in its `result.json`, and pass when the new schedule is accepted by the schedule check. A rerun can find another equally valid schedule; byte-identical results are not expected. They take minutes and are not part of `just test`.

A month's input comes from **Prüfen** after a generation (`input.json`) or from `GET /review/files/input.json`. Each month's input carries its own trusted context; supplying the preceding accepted month as context is part of preparing the sequence.

`just test` compares the published schemas with the models. A stale schema file is rewritten from its model and the test fails once, so a model change shows up as a schema diff to review and commit.

## Validate monthly and sequence results

```sh
just test tests/test_examples.py
```

The test validates the committed folders `examples/2026-01` to `examples/2026-06` and fails with the list of every problem. It accepts them only if:

- exactly these six `YYYY-MM` folders are present, each with five nonempty files, and each folder holds the bundle of its own month;
- every pair is a valid bundle as for an import (format, digest, month, references, found schedule, current rule settings, stored check equal to a re-check);
- `result.json`, `schedule.csv`, `employees.csv` and `gaps.csv` equal the rendering of the pair, so the tables contain exactly the canonical duties and every participant's account, memberships, availability and credits;
- the check is **accepted**: no finding and no blocking missing input; a month may contain declared gaps. A duty without an evidenced origin is an eligibility finding. Rejected or incomplete results are reported as _diagnostic result, not an example_;
- every month plans the same two stations and jumper pools, with duties at both stations;
- consecutive months agree: the trusted context duties of a month on the other month's dates equal that month's schedule (both directions), and the availability of the first date of the later month equals the earlier month's context availability.

Non-blocking open items stay visible in each result's check: the following month's start (checked by the next month with this schedule as context) and annual free Sundays, which need the whole year and are never reported as passed. Until the examples are committed, the example and reproduction tests are skipped; tests with small two-month bundles show that the validator accepts a consistent sequence and reports each kind of problem.

## Interpret objectives and solver settings

The check's `scores` are the objective tiers, highest first: `gaps` (unfilled required slots), health events (`six_day_windows` + `backward_transitions`), `station_transfers` (duties of station-origin employees at another station), `wish_cost` (per employee, free and preferred apart, the k-th denied grantable wish costs k³), `balance_deviation_minutes` (sum of absolute account balances) and `surplus_intermediate_duties`. `solution.stages` lists the same tiers in solving order: each stage's `value` equals its score, `status` is `optimal` or `feasible` and `best_bound` is CP-SAT's proven bound for that stage, or `null` when the stage found no schedule in its time and kept the previous one. The solution status is `optimal` only when every stage is. `configuration.timeout_seconds` is the total limit of all stages, and `configuration.policy` records every rule parameter; see the [solver reference](../architecture/solver.md). Format version 1 bundles, which carried weights and a single objective value, are not read.
