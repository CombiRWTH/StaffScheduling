# Domain model

This reference describes inspected source definitions. Connected database behavior and complete user workflows require separate acceptance evidence; see [current limitations](../validation/index.md).

`api/app/domain/` defines the canonical scheduling contract. Its Pydantic models derive from `SchedulingBaseModel`, which is frozen, forbids extra fields and strips string whitespace. The solver receives domain data rather than TimeOffice rows or frontend file schemas.

## SchedulingDataset

One `SchedulingDataset` aggregates a `PlanningMonth` and tuples of planning units, plans, shifts, dated staffing requirements, employees, memberships, Sunday work history, wishes, assignments, availability, monthly accounts and objective weights. The solver consumes it; no adapter currently builds one, and aggregate dataset validation is not implemented.

| Concept                     | Meaning and important fields                                                                           |
| --------------------------- | ------------------------------------------------------------------------------------------------------ |
| `PlanningMonth`             | Full calendar month identified by year and month                                                       |
| `PlanningUnit`              | Positive ID, display name and type: station or shared pool                                             |
| `PlanningUnitMembership`    | Employee/unit link with date validity, staffing level and home/replacement flags                       |
| `Employee`                  | Stable ID, display name, professional/assistant/trainee/MFA staffing level; legacy solver capabilities |
| `Shift`                     | ID/code/type, staffing role, start/end minutes of day and net work minutes                             |
| `DemandRequirement`         | Positive required count for a specific unit, date, shift and staffing level                            |
| `Plan`                      | Planning record associated with a unit and month                                                       |
| `Assignment`                | Employee, date, shift, assignment type and applicable unit                                             |
| `Availability`              | Constraint: unavailability, including supported date/shift limits                                      |
| `Wish`                      | Desired work/free day or shift; distinct from constraints                                              |
| `MonthlyWorkAccount`        | Target/actual minutes, optional verified credits and provenance                                        |
| `EmployeeSundayWorkHistory` | Imported Sunday work context                                                                           |
| `SolverObjectiveWeights`    | Per-unit values used by objective penalties                                                            |

Work durations and accounts use minutes; dates use calendar dates. Shift clock minutes are in `[0, 1440)`, and overnight end times can be earlier than start times. Net work time is stored separately from elapsed clock time.

A `PLANNED` assignment belongs to a selected unit and requires its unit ID. `EXTERNAL` work blocks the person without satisfying selected-unit demand and omits its source unit ID. `GENERATED` assignments represent solver output. Membership intervals determine eligibility; a shared-pool type does not create membership automatically.

## Validation and output

Model validators check individual fields and relationships. Solver-specific indexes and decision variables are derived later in `solver/cp_sat/`.

`Solution` in `api/app/solver/models.py` carries status, generated assignments, diagnostics and audit. The existing audit is implemented by solver components, not an independent acceptance checker. Canonical portable bundles and accepted CSV exports remain pending; the retired JSON file formats are not this domain contract.

For exact fields and validators, read the model modules rather than copying frontend legacy formats. [API schemas](api.md) describe HTTP DTOs; [TimeOffice](timeoffice.md) describes source translation.

## Complete employee inspection

`api/app/domain/inspection.py` composes existing canonical employee, unit, membership, account and availability models into a `PlanningInspection`. It contains one month, selected station IDs, the relevant unit catalog and one entry per stable employee ID. It exposes no plan IDs, source rows, split-name aliases or special capabilities. `associated_pool_ids` names the pools that members of the selected stations call home, computed by the same rule that adds those pools' employees. A selection that cannot be planned (a pool, an unconfigured unit or a station without a target plan) raises `InvalidSelection` instead of an incomplete-data error. Inspection validates only its own read responsibilities; it does not require staffing demand, a solve result or the full legacy dataset to be valid.

Every employee requires exactly one account and monthly evidence declaration. `WorkCredit` carries a full date, nonnegative integer minutes, `approved_absence`/`trusted_work` kind and source. Explicitly declared empty credits sum to zero; absent credit evidence remains unknown and is rejected by inspection. Actual hours never become credits. Native constraints preserve reason/source; prepared constraints retain dates and allowed-shift IDs. Foreign employee/shift references and out-of-month credit/constraint dates fail the read.

Dated home origin and dated destination membership are separate. Associated pool employees are visible even without selected-station eligibility. Active memberships need exactly one evidenced home unit on each active day. Qualifications, including MFA, are preserved at identity and membership level; they are not interchangeable. The current solver migration/independent acceptance remains separately unfinished.

Computed fields such as month start/end and account credited total are derived. Use Pydantic `model_dump(round_trip=True)` when serializing input for reparsing; do not supply derived fields as independent input.
