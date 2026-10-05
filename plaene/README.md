# Example schedules

Accepted example schedules of stations `PE 77`, `PE 78`, `PE 79`, `PE 83`, `PE 85`, `PE 88` and `PE 337` with jumper pools (Springerpools) `PE 408` and `PE 68`, January to June 2026, generated from the prepared TimeOffice test database and usable without TimeOffice.

| Folder                  | Content                                                                       |
| ----------------------- | ----------------------------------------------------------------------------- |
| `2026-01/` … `2026-06/` | The example schedules without preferences: the inputs hold no employee wishes |
| `backup/`               | An older dataset of an earlier project state; not part of these months        |

Each month folder holds one run that planned all seven stations together, with their duties combined in one `schedule.csv`. To inspect a station in a spreadsheet, filter `planning_unit_id` to its ID (77, 78, 79, 83, 85, 88 or 337). Pools 68 and 408 have no own demand or schedule: filter `origin_unit_id` to see where their staff work; their home memberships are also in `employees.csv`.

- `schedule.csv`: one row per duty.
- `employees.csv`: one row per employee in planning, also without duties.
- `besetzung.csv`: one row per station, date, shift and qualification that is required or staffed: required, assigned and missing counts.
- `gaps.csv`: the rows of `besetzung.csv` with missing slots; only the header when there are none.
- `input.json` and `result.json`: the complete input and solution, which the tests check and solve again.

Demand is adapted to the available qualifications as described in [input data](../docs/source/validation/examples.md#input-data-and-boundary-context). Large Fachkraft and Azubi gaps remain, especially where home staff and both pools cannot cover the demand. `gaps.csv` records these unfilled slots; they are never duties. A feasible gap stage does not prove the minimum gap count. The [results](../docs/source/validation/examples.md#results) give each month's measured values and bounds.

## Requested fields

| Requested                          | Column                                                                                                                                 |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Station                            | `schedule.csv` `planning_unit_id`, `planning_unit_name`                                                                                |
| Date, weekday                      | `date`, `weekday` (1 = Monday … 7 = Sunday), `is_public_holiday`                                                                       |
| Shift type, start and end          | `shift_type`, `shift_code`, `start_at`, `end_at` (Europe/Berlin with offset)                                                           |
| Employee                           | `employee_id`, `employee_name`                                                                                                         |
| Role or qualification              | `qualifikation` (Fachkraft, Hilfskraft, Azubi or MFA) and `staff_level`: the qualification the duty counts as towards minimum staffing |
| Minimum staffing each shift covers | `besetzung.csv`: `required_count`, `assigned_count` and `missing_count` per station, date, shift and `qualifikation`                   |
| Regular team or jumper pool        | `origin_unit_id`, `origin_unit_name`, `origin_unit_type` (`station` or `jumper_pool`)                                                  |
| Employee ID and link to the duties | `employees.csv` `employee_id`, equal to `employee_id` of the employee's rows in `schedule.csv`                                         |
| Station or jumper pool             | `home_unit_id`, `home_unit_name`, `home_unit_type`; every dated membership in `memberships`                                            |
| Role or qualification              | `staff_level`                                                                                                                          |
| Target time                        | `target_minutes`, with `credited_minutes`, `generated_minutes` and `balance_minutes`                                                   |
| Restrictions and availability      | `hard_availability` (JSON list of absences and shift restrictions)                                                                     |

## Check and reproduce

From the repository root:

```sh
just test tests/test_examples.py                     # validate the months and their month-to-month sequence
just test -m reproduction tests/test_examples.py     # solve every input again without TimeOffice (up to three hours)
```

Every column, the input data, the generation command and how the results are checked are described in [examples and reproduction](../docs/source/validation/examples.md); the file formats have JSON Schemas in [docs/source/validation/schema/](../docs/source/validation/schema/).
