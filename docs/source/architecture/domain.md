# Domain model

This reference describes the source definitions. Executed live checks are listed under [current limitations](../validation/index.md).

`api/app/domain/` defines the canonical scheduling contract. Its Pydantic models derive from `SchedulingBaseModel`, which is frozen, forbids extra fields and strips string whitespace. The solver receives domain data rather than TimeOffice rows or frontend file schemas.

## SchedulingDataset

One `SchedulingDataset` is the complete input of one full-month run: a `PlanningMonth`, the planning units (selected stations and their associated jumper pools), shifts, dated demand requirements, employees, memberships, availability, wishes, one monthly account per employee and the trusted `ScheduleContext`. It validates all references once:

- unique identities and exactly one account per employee,
- demand only for its stations and shifts inside the month,
- context inside its coverage and outside the month,
- unambiguous Europe/Berlin times for every shift on every date of the month,
- at most one wish per employee and date, inside the month, for a known shift,
- every membership naming one of its units, with exactly one home membership on each date an employee has any,
- every credit inside the month.

An imported input therefore cannot carry an ambiguous origin or count a credit twice. `build_scheduling_dataset` (`dataset.py`) builds the dataset from a validated employee inspection, the timed reference shifts, each selected station's saved demand, the context and the inspected employees' wishes. It refuses a station without saved demand.

| Concept                  | Meaning and important fields                                                                                            |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `PlanningMonth`          | Full calendar month identified by year and month                                                                        |
| `PlanningUnit`           | Positive ID, display name and type: station or jumper pool                                                              |
| `PlanningUnitMembership` | Employee/unit link with date validity, qualification and home/replacement flags                                         |
| `Employee`               | Stable ID, display name and employee-level qualification (professional, assistant, trainee, MFA)                        |
| `Shift`                  | ID, code, type, work `segments` and paid `net_work_minutes`; start and end derive from the segments                     |
| `DemandRequirement`      | Positive required count for a specific station, date, shift and qualification                                           |
| `Gap`                    | Required slots of one demand row that no assignment fills (`missing_count`); reported, never published                  |
| `Assignment`             | Employee, start date, station, shift and the qualification (`staff_level`) the duty is credited as                      |
| `ScheduleContext`        | Trusted duties outside the month, their coverage `covered_from`–`covered_until`, availability of the date after         |
| `Availability`           | Binding date entry: unavailable/vacation/training/free day, or only listed shifts                                       |
| `Wish`                   | Soft free/preferred day or shift of one employee and date at any station; considered by generation, never binding       |
| `MonthlyWorkAccount`     | Target, informational actual minutes and the month's dated credits; `balance(generated)` = generated + credits − target |

Durations and accounts use whole minutes; dates are calendar dates. A `WorkSegment` gives local minutes after midnight of the duty's start date, so an overnight segment ends after 1440; the gaps between segments are unpaid breaks. A shift starts on its start date and lasts less than 24 hours. `duty.py` turns a date and shift into UTC instants: elapsed work changes on a daylight-saving night, paid minutes do not. `RulePolicy` in `rules.py` holds the hard-rule parameters; see the [solver](solver.md).

An assignment's qualification comes from the employee's membership at that station on that date, which can differ from the employee-level qualification. Membership intervals determine eligibility; a jumper-pool membership alone never does.

## Validation and output

Model validators check individual fields and relationships. `acceptance.py` holds the independent schedule check `check_schedule(dataset, assignments, gaps)`, returning a `ScheduleCheck` with status (`accepted`, `rejected`, `incomplete`), findings per `Rule`, not-assessed obligations, `ScheduleScores` and the outcome of every wish; a declared gap that differs from the recomputed shortfall is a staffing finding. `Solution` in `api/app/solver/models.py` carries the solver status, configuration, assignments, gaps, stages, diagnostics and that check.

For exact fields and validators, read the model modules. [API schemas](api.md) describe HTTP DTOs; [TimeOffice](timeoffice.md) describes source translation.

## Schedule tables

`schedule_tables` (`schedule.py`) turns a dataset and its assignments into `ScheduleTables`, the readable rows that the review and the portable CSV files of `api/app/solver/bundle.py` share: a `DutyRow` per assignment (labels, ISO weekday, public-holiday flag, Europe/Berlin start and end with offset, paid minutes, credited qualification and origin), an `EmployeeRow` per participant also without duties (home station or jumper pool of the first date that has one, target, credited, generated minutes, balance, memberships, availability and credits) and a `CoverageRow` per station, date, shift and qualification that is required or assigned, with its missing count; `gaps` are the coverage rows with missing slots. The origin is the employee's home station or jumper pool on the duty date (`home_unit_id`); more than one active home raises instead of guessing.

## Complete employee inspection

`api/app/domain/inspection.py` composes existing canonical employee, unit, membership, account and availability models into a `PlanningInspection`. It contains one month, selected station IDs, the relevant unit catalog and one entry per stable employee ID. It exposes no plan IDs or source rows. `associated_jumper_pool_ids` names the jumper pools that members of the selected stations call home, computed by the same rule that adds those jumper pools' employees. A selection that cannot be planned (a jumper pool, an unconfigured unit or a station without a target plan) raises `InvalidSelection` instead of an incomplete-data error. Inspection validates only its own read responsibilities; it does not require staffing demand or a solve result to be valid.

Every employee requires exactly one account. `WorkCredit` carries a full date, nonnegative integer minutes, `approved_absence`/`trusted_work` kind and source; an account's `credit_details` are complete for the month, and an empty tuple means nothing is credited. The adapter fills them from its source, so a missing credit is a source problem, not an optional field. Actual hours never become credits. Native absences preserve their reason and source; project availability retains dates, allowed-shift IDs and reason. Unknown shifts and out-of-month credit or availability dates fail the read.

Dated home origin and dated destination membership are separate. Associated jumper pool employees are visible even without selected-station eligibility. Active memberships need exactly one evidenced home unit on each active day. Qualifications, including MFA, are preserved at identity and membership level; they are not interchangeable.

Computed fields such as month start/end and account credited total are derived. Use Pydantic `model_dump(round_trip=True)` when serializing input for reparsing; do not supply derived fields as independent input.

## Monthly configuration

`availability.py` holds `AvailabilityEntry` (type, allowed shifts, reason and their rules), `Availability` (an entry plus employee, date and `native_absence`, set for a read-only TimeOffice absence whose reason is its code) and `EmployeeCalendar`, an employee month of read-only native `absences`, editable `availability` and `wishes` plus the month's calendar and the reference `ShiftOption`s. `EmployeeSummary` (ID and name) is what choosing an employee needs. An `available_only` entry needs distinct `shift_ids`; other types must not have any. A `WishEntry` carries the wish type and its shift rule; a `Wish` adds employee and date. Writes take an entry and the employee/date key, so request bodies are validated before the service is called.

`calendar.py` derives the planning calendar: every date of a month with its ISO weekday and North Rhine-Westphalia public holiday from the `holidays` package. A holiday keeps its weekday; its `DayType` is `holiday`.

`demand.py` holds `DemandCell` (date, shift, qualification, count 1–99), `MonthlyDemand` (one station month whose cells are unique per date/shift/qualification and inside the month; its `requirements` property gives the solver's station-qualified `DemandRequirement`s), `DemandConfiguration` (the editor's read: saved demand or `None`, calendar and shifts) and `DemandPattern`. `expand_pattern` applies a weekly pattern to every date, using the holiday row on public holidays and dropping zero cells. MFA is its own staff level and never stands in for Hilfskraft.
