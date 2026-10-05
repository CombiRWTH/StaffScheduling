# Examples and reproduction

For readers trying to inspect or reproduce the example schedules in `plaene/`. They were generated from the prepared TimeOffice inputs below and can be checked and solved again without TimeOffice. All six months are committed (`plaene/2026-01` to `plaene/2026-06`), each accepted by the schedule check.

Return to the [documentation overview](../index.md).

## Example scope and file inventory

Stations `PE 77`, `PE 78`, `PE 79`, `PE 83`, `PE 85`, `PE 88` and `PE 337` of the TimeOffice test database with jumper pools `PE 408` and `PE 68`, planned together for each month from January to June 2026: 42 station months. The pools receive no schedule of their own; their employees work at eligible stations. The units and their keys are listed in the [adapter reference](../architecture/timeoffice.md#prepared-units).

Each month is a folder `plaene/2026-MM/` with the six [bundle files](#bundle-files): the requested example schedules without preferences ("ohne Präferenzen"). `plaene/backup/` holds an older dataset of an earlier project state (stations 77 and 78, another format). It is not an input of these months and not checked by the tests below.

## Input data and boundary context

The employees are the units' existing test-database employees, all of them adults; the test database holds no real persons. Their contracts, home memberships and native targets are used unchanged. In scope every month: 96 employees (77 station staff, 19 jumper pool), by employee profession 76 professionals, 13 assistants, 1 MFA and 6 trainees. A duty counts as the qualification of the dated station membership, which can differ from the employee record. Everything else is prepared by the tracked SQL in `api/tests/timeoffice_preparation/`; [reproduce the inputs](#reproduce-the-timeoffice-inputs) below.

- **Eligibility.** Station staff are members of their station. Pool 408 serves all seven stations; pool 68 serves 78, 83, 85, 88 and 337. Their staff have the pool as home and replacement memberships at these stations from 2025-12-01 to 2026-07-31. Rotating trainees, whose home is a school unit and who are station members for part of a month only, are excluded from planning (`KeinEPlan`).
- **Targets.** Native targets are kept. Missing ones are derived by the native rule: weekly hours (38.5 when the contract states none) ÷ 5 for each Monday–Friday that is not an NRW public holiday.
- **Absences.** Each professional of stations 77 and 79 and pool 408, and each assistant and the MFA of `PE 77`, has one Monday–Friday vacation week (`U`), credited with the weekly hours ÷ 5 per day in TimeOffice's daily accounts. Pool 408's vacations fall in June. No additional vacations were added for the other stations or pool 68.
- **Demand.** Fachkraft demand follows the chair's minimum-staffing CSV at all stations; NRW public holidays use its weekend row. At the additional stations, trainee demand also follows the CSV. At 77 it remains one early trainee on weekdays; 79 has none. Only pool 408's trainee can serve all seven stations. Assistant demand is adapted to the staff: 78 and 85 one early duty Monday–Friday, 337 none, 77 early 2 and late 2 on weekdays (early 2, late 1 on weekends/holidays), and 79 one early every day. MFA demand is one early duty on weekdays at 77 and none at the other stations, where no MFA is eligible. Qualifications stay separate.
- **Capacity and gaps.** Stations 83, 85, 88 and 337 have a Fachkraft shortfall before the pools are allocated; 88 requires 14 professional duties daily for five home professionals, and 337 three for one. Both pools together cannot cover all professional and trainee demand. Home-station staff can only serve their own station, so surplus staff at 77/78/79 cannot fill another station's gaps. The hard monthly balance also requires surplus duties. The sole MFA's vacation week, 2026-02-09..13, leaves five unavoidable gaps. Further gaps can follow from rest rules and the previous month's last duties. The solver's gap count is feasible unless its gap stage is `optimal`; an unproven count must not be read as the minimum required guest staffing. See the measured [results](#results).
- **Boundary context.** Empty trusted context plans cover 2025-12-18 to 2025-12-31 and 2026-07-01 to 2026-07-07: January starts and June ends next to known free days. From February, the [generation](#generate-the-examples) takes the last five days of the accepted previous month as trusted context.
- **Availability.** One employee is unavailable on 2026-06-08..12, where native duties remain in the June target plan; two employees may work only early (2026-03-10) or early and intermediate shifts (2026-04-14).
- **Not included.** Special capabilities, replacement memberships of station staff and history before 2025-12-18. Annual free Sundays need the whole year and cannot be assessed from this data.

## Reproduce the TimeOffice inputs

With the [database configuration](../getting-started/installation.md#database-configuration) for the authorized test database and Docker:

```sh
just test-timeoffice                                   # verify: every file converged, every check ok
TIMEOFFICE_PREPARATION=apply just test-timeoffice      # prepare a copy that lacks the inputs, then verify again
```

The verification runs each preparation file in one transaction, fails on any read-back other than `ok` = 1 or any write that would change a row, and rolls back. Apply commits the files in order; each is committed only when its read-back is ok, and a failing file stops the run with the later files unapplied. Then open **Mitarbeiter** for all seven stations and each month: the inspection must be complete. There is no reverse script; on a shared database, record what a first apply writes before running it.

## Bundle files

A monthly bundle is one folder `YYYY-MM/` with six files, as downloaded from **Prüfen**. JSON is the complete reproduction format; the CSV tables are the readable submission format and are derived from the JSON pair, never read back.

| File            | Content                                                                                                                                                                                                                                                                                                                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `input.json`    | `format_version` (3), `timezone` (`Europe/Berlin`), the month's `calendar` (date, ISO weekday Monday=1, NRW public holiday name) and the canonical `dataset`: stations and jumper pools, shifts with work segments and paid minutes, dated demand, employees, dated memberships, binding availability, wishes, monthly accounts with dated credits and the trusted context with its coverage                                          |
| `result.json`   | `format_version`, `planning_month`, `input` (`file` and hex `sha256` of the exact `input.json` bytes), the `solution` (CP-SAT status, effective configuration with rule policy, total timeout, workers and seed, wall time, assignments, gaps, every objective stage with value, status and bound, diagnostics and the independent `check` with scores and wish outcomes) and the solving `versions` of Python, OR-Tools and Pydantic |
| `schedule.csv`  | One row per duty, sorted by date, station, start and employee                                                                                                                                                                                                                                                                                                                                                                         |
| `employees.csv` | One row per participating employee, also without duties, sorted by ID                                                                                                                                                                                                                                                                                                                                                                 |
| `besetzung.csv` | One row per station, date, shift and qualification that is required or staffed: the required, assigned and missing counts, sorted by station, date, shift and qualification                                                                                                                                                                                                                                                           |
| `gaps.csv`      | The rows of `besetzung.csv` with missing slots; only the header when there are none                                                                                                                                                                                                                                                                                                                                                   |

The JSON Schemas are generated from the Pydantic models: [input.schema.json](schema/input.schema.json) and [result.schema.json](schema/result.schema.json). Parsing rejects unknown fields, other format versions and a calendar that is not the month's NRW calendar. Derived values (month start/end, credited totals, health events, wish counts) are left out of the files and recomputed. There is no TimeOffice plan, credential or SQL row; IDs are the canonical positive numbers.

`schedule.csv` columns: `employee_id`, `employee_name`, `date`, `weekday` (ISO numbering, 1 = Monday to 7 = Sunday), `is_public_holiday`, `planning_unit_id` and `planning_unit_name` (the station where the duty is worked), `shift_id`, `shift_code`, `shift_type`, `start_at` and `end_at` (ISO 8601 with Europe/Berlin offset; a night ends on the next date and a duty belongs to its start date), `net_work_minutes` (paid), `staff_level` (the [credited qualification](../glossary.md#schedules)) and `qualifikation` (its German name: `Fachkraft`, `Hilfskraft`, `Azubi` or `MFA`), and `origin_unit_id`, `origin_unit_name`, `origin_unit_type` (the employee's home station or jumper pool on that date; `station` for the regular team, `jumper_pool` for the Springerpool).

`employees.csv` columns: `employee_id`, `employee_name`, `staff_level` (employee level), `home_unit_id`, `home_unit_name` and `home_unit_type` (`station` or `jumper_pool`: the employee's home station or jumper pool on the first date of the month that has one), `planning_month` (`YYYY-MM`), `target_minutes`, `credited_minutes`, `generated_minutes`, `balance_minutes` (generated + credited − target), and `memberships`, `hard_availability`, `credit_details`: complete JSON arrays copied from the input, in quoted cells. `memberships` lists every dated membership with its qualification, `is_home` and `is_replacement` (a jumper pool employee's Ersatz membership at a station); `hard_availability` every binding absence or restriction of the month (`date`, `availability_type`, `reason`, the allowed `shift_ids` of `available_only`, `native_absence` for a TimeOffice absence); `credit_details` every credit (`date`, `minutes`, `kind` `approved_absence` or `trusted_work`, `source`).

`besetzung.csv` and `gaps.csv` columns: `planning_unit_id`, `planning_unit_name`, `date`, `shift_id`, `shift_code`, `staff_level`, `qualifikation`, `required_count` (the demand; 0 for a staffed shift without demand, often an intermediate shift), `assigned_count` (duties credited as this qualification; it may exceed the demand) and `missing_count` (required − assigned, at least 0). Every duty counts in exactly one row. Gaps are never duties; they name the slots for which guest staff is needed.

Wish outcomes stay in `result.json` (`solution.check.wishes`, each wish with `status` `granted`, `denied` or `not_grantable`); they are not a CSV table.

CSV conventions: UTF-8, comma, one header row, standard-library quoting, `\n` line ends, `true`/`false` booleans, integer minutes, full ISO dates. An empty cell only appears in the origin columns, for a duty of an employee without membership that day, which the check reports as an eligibility finding.

## Generate the examples

With the prepared inputs, the database configuration and Docker, from the repository root:

```sh
PLAENE_GENERATION=write just test-timeoffice tests/test_examples.py
```

The command generates January to June in order, each month read from TimeOffice for stations 77, 78, 79, 83, 85, 88 and 337 like a generation in the webapp and solved for 1,800 seconds with the default solver settings. TimeOffice is only read; nothing is written back. The inputs are used as read, wishes included; the examples are without preferences because the prepared inputs hold no wishes. From February, the month's trusted context is the last five days of the accepted previous month, in place of TimeOffice context plans, which exist only before January and after June. A month is written only when its check is accepted; otherwise the run stops with the month's status and blocking items. An existing month folder for these seven stations is kept and serves as the next month's context; a folder for another selection is rejected, so a run continues after the last written month; delete a month's folder and the later ones to generate them again. The run ends with the validation below.

## Results

Generated on 2026-10-05 with the seven-station generation settings committed in `f3c6262`, 1,800 seconds per month, default solver settings, in the API image (Linux arm64 container on macOS). Every month includes 96 employees, is wish-free, and is **accepted** with 0 findings. No station-origin employee transfers. Health events count six-day windows, backward transitions, isolated workdays and back-to-back worked weekends; balance is the sum of absolute monthly balances.

| Month | Duties | Jumper pool duties | Gap slots | Gap bound | Health events | Balance minutes | Surplus intermediate |
| ----- | -----: | -----------------: | --------: | --------: | ------------: | --------------: | -------------------: |
| Jan   |   1849 |                326 |       484 |       461 |           290 |           16434 |                  152 |
| Feb   |   1744 |                309 |       411 |       403 |           317 |           14198 |                  136 |
| Mar   |   1916 |                346 |       461 |       445 |           525 |           20740 |                  143 |
| Apr   |   1794 |                310 |       479 |       455 |           257 |           10561 |                  182 |
| May   |   1614 |                278 |       588 |       548 |           417 |           17619 |                  131 |
| Jun   |   1831 |                299 |       477 |       456 |           452 |           14876 |                  116 |

Every gap stage is `feasible`, with the shown proven lower bound. Neither gap counts nor health, balance and surplus scores are proven optimal. A longer January gate improved gaps from 512 at 900 seconds to 484 at 1,800 seconds (bound 461), health from 425 to 290, and balance from 24,409 to 16,434 minutes. The seven-station model therefore uses 1,800 seconds instead of the earlier two-station limit of 300 seconds. The values below are the observed unfilled slots, not a proof of the minimum guest staffing needed. Readiness estimates from hours are approximate: shift lengths and the permitted monthly account deviation affect the attainable number of duties.

### Gaps by station and qualification

| Station | Qualification | Jan | Feb | Mar | Apr | May | Jun |
| ------: | ------------- | --: | --: | --: | --: | --: | --: |
|      77 | Azubi         |  21 |  19 |  21 |  17 |  18 |  17 |
|      77 | MFA           |   0 |   5 |   2 |   0 |   0 |   0 |
|      78 | Azubi         |  60 |  51 |  58 |  57 |  61 |  58 |
|      78 | Hilfskraft    |   0 |   2 |   0 |   0 |   0 |   0 |
|      83 | Azubi         |  55 |  52 |  56 |  57 |  59 |  56 |
|      83 | Fachkraft     |  67 |  51 |  54 |  69 |  90 |  64 |
|      85 | Azubi         |  54 |  53 |  58 |  56 |  57 |  53 |
|      85 | Fachkraft     |   4 |   0 |   1 |   1 |  12 |   2 |
|      88 | Fachkraft     | 143 | 116 | 132 | 148 | 222 | 152 |
|     337 | Azubi         |  55 |  46 |  52 |  50 |  51 |  53 |
|     337 | Fachkraft     |  25 |  16 |  27 |  24 |  18 |  22 |

Station 79 has no gaps in any month. Stations 77 and 78 retain trainee gaps; 77's February MFA gaps are its vacation week, and its March MFA gaps on March 2–3 follow the February 28 night duty: the 48-hour recovery ends at 06:10 on March 3, after the early shift's 05:55 start. Station 78 also has two assistant gaps on February 2–3. Stations 83, 85, 88 and 337 retain Fachkraft gaps, largest at 88, as well as trainee gaps where demand exists. Pool 408's trainee is shared across all stations; pool 68 adds no trainee. The [input data](#input-data-and-boundary-context) explains the demand adaptations and structural shortfalls; every missing date and shift is in `gaps.csv`.

## Reproduce without TimeOffice

From the repository root, with the [native tools](../getting-started/installation.md#optional-native-developer-setup) installed:

```sh
just test -m reproduction tests/test_examples.py
```

The reproduction tests solve every committed `input.json` again with the time limit, search workers and seed recorded in its `result.json`, and pass when the new schedule is accepted by the schedule check. A rerun can find another equally valid schedule; byte-identical results are not expected. Each month takes up to its recorded 1,800 seconds, about three hours for all six, so they are not part of `just test`; `-k 2026-03` selects one month. The months were generated without a fixed seed and with CP-SAT's default number of workers, so a rerun on another machine searches differently; what is reproduced is an accepted schedule, not the same objective values.

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
- no input holds wishes, so the schedules are without preferences;
- every month plans the same seven stations and two jumper pools, with duties at every station;
- consecutive months agree: the trusted context duties of a month on the other month's dates equal that month's schedule (both directions), and the availability of the first date of the later month equals the earlier month's context availability.

Non-blocking open items stay visible in each result's check: the following month's start (checked by the next month with this schedule as context) and annual free Sundays, which need the whole year and are never reported as passed. The committed months pass. Tests with small two-month bundles show that the validator accepts a consistent sequence and reports each kind of problem.

## Interpret objectives and solver settings

The check's `scores` are the objective tiers, highest first: `gaps` (unfilled required slots), health events (`six_day_windows` + `backward_transitions` + `isolated_workdays` + `back_to_back_weekends`), `station_transfers` (duties of station-origin employees at another station), `wish_cost` (per employee, free and preferred apart, the k-th denied grantable wish costs k³), `balance_deviation_minutes` (sum of absolute account balances) and `surplus_intermediate_duties`. `solution.stages` lists the same tiers in solving order: each stage's `value` equals its score, `status` is `optimal` or `feasible` and `best_bound` is CP-SAT's proven bound for that stage, or `null` when the stage found no schedule in its time and kept the previous one. The solution status is `optimal` only when every stage is. `configuration.timeout_seconds` is the total limit of all stages, and `configuration.policy` records every rule parameter; see the [solver reference](../architecture/solver.md). Bundles of earlier format versions are not read.
