# Examples and reproduction

For readers trying to inspect or reproduce the example schedules in `plaene/`. They were generated from the prepared TimeOffice inputs below and can be checked and solved again without TimeOffice. All six months are committed (`plaene/2026-01` to `plaene/2026-06`), each accepted by the schedule check.

Return to the [documentation overview](../index.md).

## Example scope and file inventory

Stations `PE 77` and `PE 79` of the TimeOffice test database and their jumper pool `PE 408`, planned together for each month from January to June 2026: twelve station months. The units and their keys are listed in the [adapter reference](../architecture/timeoffice.md#prepared-units).

Each month is a folder `plaene/2026-MM/` with the six [bundle files](#bundle-files): the requested example schedules without preferences ("ohne Präferenzen"). `plaene/backup/` holds an older dataset of an earlier project state (stations 77 and 78, another format). It is not an input of these months and not checked by the tests below.

## Input data and boundary context

The employees are the units' existing test-database employees, all of them adults; the test database holds no real persons. Their contracts, home memberships and native targets are used unchanged. In scope every month: 53 employees (46 station staff, 7 jumper pool), by profession 40 professionals, 8 assistants, 1 MFA and 4 trainees. Everything else is prepared by the tracked SQL in `api/tests/timeoffice_preparation/`; [reproduce the inputs](#reproduce-the-timeoffice-inputs) below.

- **Eligibility.** Station staff are members of their station. The jumper pool staff have the jumper pool as home and replacement memberships at both stations from 2025-12-01 to 2026-07-31. Rotating trainees, whose home is a school unit and who are station members for part of a month only, are excluded from planning (`KeinEPlan`).
- **Targets.** Native targets are kept. Missing ones are derived by the native rule: weekly hours (38.5 when the contract states none) ÷ 5 for each Monday–Friday that is not an NRW public holiday.
- **Absences.** Each professional of both stations and the jumper pool, and each assistant and the MFA of `PE 77`, has one Monday–Friday vacation week (`U`), credited with the weekly hours ÷ 5 per day in TimeOffice's daily accounts. The jumper pool's vacations fall in June.
- **Demand.** Professionals follow the chair's minimum-staffing table for keys 77 and 79 (its weekday and weekend/holiday rows; NRW holidays take the weekend row). The table's other levels exceed the real staff, so they are sized near it, so that the jumper pool visibly jumps and gaps stay small: at `PE 77` assistants early 2 and late 2 on weekdays (early 2, late 1 on weekends and holidays), one trainee and one MFA early on weekdays; at `PE 79` one assistant early every day and no trainee or MFA demand. Qualifications stay separate.
- **Capacity.** Per qualification and month, available hours (target − credits) of the home staff against demand hours are 1.37–1.65 for professionals at `PE 77`, 1.03–1.26 at `PE 79`, and 0.64–1.12 for assistants; the trainee demand at `PE 77` relies on the jumper pool's trainee alone. Every shortfall is smaller than the jumper pool's hours of that qualification. The one deliberate gap is the MFA's vacation week, 2026-02-09..13: no other MFA exists, so its early demand stays unfilled for five days. This is an hours and headcount check only; it does not show that a schedule satisfying every rule exists. The generated months show further gaps where a month's end constrains the next month's start: March has early-shift gaps at `PE 77` for the MFA and a trainee on 2026-03-02 and 03-03, because February, solved without knowing March, ends with night duties of the only MFA and of trainees on 2026-02-28, and the 48-hour recovery after a night run lasts until 06:10 on 2026-03-03, after the early shift's 05:55 start. The gap stage is optimal, so no March schedule avoids them given that context.
- **Boundary context.** Empty trusted context plans cover 2025-12-18 to 2025-12-31 and 2026-07-01 to 2026-07-07: January starts and June ends next to known free days. From February, the [generation](#generate-the-examples) takes the last five days of the accepted previous month as trusted context.
- **Availability.** One employee is unavailable on 2026-06-08..12, where native duties remain in the June target plan; two employees may work only early (2026-03-10) or early and intermediate shifts (2026-04-14).
- **Wishes.** 32 demonstration wishes: two per station and month and one of a jumper pool employee per month, covering free days, free shifts, preferred days and preferred shifts. Two are not grantable by design: a late shift on the early-only day 2026-03-10, and a wish on 2026-03-25 inside the employee's own vacation.
- **Not included.** Stations 78 and 85, special capabilities, replacement memberships of station staff and history before 2025-12-18. Annual free Sundays need the whole year and cannot be assessed from this data.

## Reproduce the TimeOffice inputs

With the [database configuration](../getting-started/installation.md#database-configuration) for the authorized test database and Docker:

```sh
just test-timeoffice                                   # verify: every file converged, every check ok
TIMEOFFICE_PREPARATION=apply just test-timeoffice      # prepare a copy that lacks the inputs, then verify again
```

The verification runs each preparation file in one transaction, fails on any read-back other than `ok` = 1 or any write that would change a row, and rolls back. Apply commits the files in order; each is committed only when its read-back is ok, and a failing file stops the run with the later files unapplied. Then open **Mitarbeiter** for both stations and each month: the inspection must be complete. There is no reverse script; on a shared database, record what a first apply writes before running it.

## Bundle files

A monthly bundle is one folder `YYYY-MM/` with six files, as downloaded from **Prüfen**. JSON is the complete reproduction format; the CSV tables are the readable submission format and are derived from the JSON pair, never read back.

| File            | Content                                                                                                                                                                                                                                                                                                                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `input.json`    | `format_version` (3), `timezone` (`Europe/Berlin`), the month's `calendar` (date, ISO weekday Monday=1, NRW public holiday name) and the canonical `dataset`: stations and jumper pools, shifts with work segments and paid minutes, dated demand, employees, dated memberships, binding availability, wishes, monthly accounts with dated credits and the trusted context with its coverage                                          |
| `result.json`   | `format_version`, `planning_month`, `input` (`file` and hex `sha256` of the exact `input.json` bytes), the `solution` (CP-SAT status, effective configuration with rule policy, total timeout, workers and seed, wall time, assignments, gaps, every objective stage with value, status and bound, diagnostics and the independent `check` with scores and wish outcomes) and the solving `versions` of Python, OR-Tools and Pydantic |
| `schedule.csv`  | One row per duty, sorted by date, station, start and employee                                                                                                                                                                                                                                                                                                                                                                         |
| `employees.csv` | One row per participating employee, also without duties, sorted by ID                                                                                                                                                                                                                                                                                                                                                                 |
| `besetzung.csv` | One row per station, date, shift and qualification with staffing demand: the required, assigned and missing counts, sorted by station, date, shift and qualification                                                                                                                                                                                                                                                                  |
| `gaps.csv`      | The rows of `besetzung.csv` with missing slots; only the header when there are none                                                                                                                                                                                                                                                                                                                                                   |

The JSON Schemas are generated from the Pydantic models: [input.schema.json](schema/input.schema.json) and [result.schema.json](schema/result.schema.json). Parsing rejects unknown fields, other format versions and a calendar that is not the month's NRW calendar. Derived values (month start/end, credited totals, health events, wish counts) are left out of the files and recomputed. There is no TimeOffice plan, credential or SQL row; IDs are the canonical positive numbers.

`schedule.csv` columns: `employee_id`, `employee_name`, `date`, `weekday` (ISO numbering, 1 = Monday to 7 = Sunday), `is_public_holiday`, `planning_unit_id` and `planning_unit_name` (the station where the duty is worked), `shift_id`, `shift_code`, `shift_type`, `start_at` and `end_at` (ISO 8601 with Europe/Berlin offset; a night ends on the next date and a duty belongs to its start date), `net_work_minutes` (paid), `staff_level` (the [credited qualification](../glossary.md#schedules)) and `qualifikation` (its German name: `Fachkraft`, `Hilfskraft`, `Azubi` or `MFA`), and `origin_unit_id`, `origin_unit_name`, `origin_unit_type` (the employee's home station or jumper pool on that date; `station` for the regular team, `jumper_pool` for the Springerpool).

`employees.csv` columns: `employee_id`, `employee_name`, `staff_level` (employee level), `home_unit_id`, `home_unit_name` and `home_unit_type` (`station` or `jumper_pool`: the employee's home station or jumper pool on the first date of the month that has one), `planning_month` (`YYYY-MM`), `target_minutes`, `credited_minutes`, `generated_minutes`, `balance_minutes` (generated + credited − target), and `memberships`, `hard_availability`, `credit_details`: complete JSON arrays copied from the input, in quoted cells. `memberships` lists every dated membership with its qualification, `is_home` and `is_replacement` (a jumper pool employee's Ersatz membership at a station); `hard_availability` every binding absence or restriction of the month (`date`, `availability_type`, `reason`, the allowed `shift_ids` of `available_only`, `native_absence` for a TimeOffice absence); `credit_details` every credit (`date`, `minutes`, `kind` `approved_absence` or `trusted_work`, `source`).

`besetzung.csv` and `gaps.csv` columns: `planning_unit_id`, `planning_unit_name`, `date`, `shift_id`, `shift_code`, `staff_level`, `qualifikation`, `required_count` (the demand), `assigned_count` (duties credited as this qualification; it may exceed the demand) and `missing_count` (required − assigned, at least 0). A duty whose station, date, shift and qualification have no demand, often an intermediate shift, counts towards no row. Gaps are never duties; they name the slots for which guest staff is needed.

Wish outcomes stay in `result.json` (`solution.check.wishes`, each wish with `status` `granted`, `denied` or `not_grantable`); they are not a CSV table.

CSV conventions: UTF-8, comma, one header row, standard-library quoting, `\n` line ends, `true`/`false` booleans, integer minutes, full ISO dates. An empty cell only appears in the origin columns, for a duty of an employee without membership that day, which the check reports as an eligibility finding.

## Generate the examples

With the prepared inputs, the database configuration and Docker, from the repository root:

```sh
PLAENE_GENERATION=write just test-timeoffice tests/test_examples.py
```

The command generates January to June in order, each month read from TimeOffice for stations 77 and 79 like a generation in the webapp and solved for 300 seconds with the default solver settings. TimeOffice is only read; nothing is written back. The inputs are used as read, wishes included; the examples are without preferences because the prepared inputs hold no wishes. From February, the month's trusted context is the last five days of the accepted previous month, in place of TimeOffice context plans, which exist only before January and after June. A month is written only when its check is accepted; otherwise the run stops with the month's status and blocking items. An existing month folder is kept and serves as the next month's context, so a run continues after the last written month; delete a month's folder and the later ones to generate them again. The run ends with the validation below.

## Results

The months, generated on 2026-10-02 at revision `4b6b2fa` (the generation code; the inputs come from the prepared test database), 300 seconds per month, default solver settings, in the API image (Linux arm64 container on macOS). Health events count six-day windows, backward transitions, isolated workdays and back-to-back worked weekends; the balance is the sum of absolute monthly balances. Every month's check is `accepted` with 0 findings, its gap stage is optimal and no station-origin employee transfers.

| Month | Duties | Jumper pool duties | Gap slots | Health events | Balance minutes | Surplus intermediate |
| ----- | -----: | -----------------: | --------: | ------------: | --------------: | -------------------: |
| Jan   |   1042 |                157 |         0 |            34 |             497 |                  219 |
| Feb   |    951 |                145 |         5 |            72 |            4928 |                  138 |
| Mar   |   1051 |                160 |         4 |           128 |            5414 |                  121 |
| Apr   |    991 |                148 |         0 |            64 |            4953 |                  158 |
| May   |    928 |                138 |         0 |            49 |            1461 |                  198 |
| Jun   |   1022 |                132 |         0 |            64 |            3384 |                  189 |

On 2026-10-05 the committed months were carried to format 3 without solving again: only the format version and the input digest changed, and `besetzung.csv` and the `qualifikation` column were rendered from the unchanged pair.

February's gaps are the MFA's vacation week and March's follow from February's last nights ([input data](#input-data-and-boundary-context)). The later stages stop at the time limit as `feasible`, so their values are not proven minimal: March's 128 health events include 73 back-to-back worked weekends.

## Reproduce without TimeOffice

From the repository root, with the [native tools](../getting-started/installation.md#optional-native-developer-setup) installed:

```sh
just test -m reproduction tests/test_examples.py
```

The reproduction tests solve every committed `input.json` again with the time limit, search workers and seed recorded in its `result.json`, and pass when the new schedule is accepted by the schedule check. A rerun can find another equally valid schedule; byte-identical results are not expected. Each month takes its recorded 300 seconds, about half an hour for all six, so they are not part of `just test`; `-k 2026-03` selects one month. The months were generated without a fixed seed and with CP-SAT's default number of workers, so a rerun on another machine searches differently; what is reproduced is an accepted schedule, not the same objective values.

Each month's `input.json` carries its own trusted context, so every month solves on its own.

`just test` compares the published schemas with the models. A stale schema file is rewritten from its model and the test fails once, so a model change shows up as a schema diff to review and commit.

## Validate monthly and sequence results

```sh
just test tests/test_examples.py
```

The test validates the committed months `plaene/2026-01` to `plaene/2026-06` and fails with the list of every problem. It accepts them only if:

- exactly these six `YYYY-MM` folders are present (other folders such as `backup/` are ignored), each with six nonempty files, and each folder holds the bundle of its own month;
- every pair is a valid bundle as for an import (format, digest, month, references, found schedule, current rule settings, stored check equal to a re-check);
- `result.json`, `schedule.csv`, `employees.csv`, `besetzung.csv` and `gaps.csv` equal the rendering of the pair, so the tables contain exactly the canonical duties and every participant's account, memberships, availability and credits;
- the check is **accepted**: no finding and no blocking missing input; a month may contain declared gaps. A duty without an evidenced origin is an eligibility finding. Rejected or incomplete results are reported as _diagnostic result, not an example_;
- every month plans the same two stations and jumper pools, with duties at both stations;
- consecutive months agree: the trusted context duties of a month on the other month's dates equal that month's schedule (both directions), and the availability of the first date of the later month equals the earlier month's context availability.

Non-blocking open items stay visible in each result's check: the following month's start (checked by the next month with this schedule as context) and annual free Sundays, which need the whole year and are never reported as passed. The committed months pass. Tests with small two-month bundles show that the validator accepts a consistent sequence and reports each kind of problem.

## Interpret objectives and solver settings

The check's `scores` are the objective tiers, highest first: `gaps` (unfilled required slots), health events (`six_day_windows` + `backward_transitions` + `isolated_workdays` + `back_to_back_weekends`), `station_transfers` (duties of station-origin employees at another station), `wish_cost` (per employee, free and preferred apart, the k-th denied grantable wish costs k³), `balance_deviation_minutes` (sum of absolute account balances) and `surplus_intermediate_duties`. `solution.stages` lists the same tiers in solving order: each stage's `value` equals its score, `status` is `optimal` or `feasible` and `best_bound` is CP-SAT's proven bound for that stage, or `null` when the stage found no schedule in its time and kept the previous one. The solution status is `optimal` only when every stage is. `configuration.timeout_seconds` is the total limit of all stages, and `configuration.policy` records every rule parameter; see the [solver reference](../architecture/solver.md). Bundles of earlier format versions are not read.
