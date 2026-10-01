# Domain model

`api/app/domain/` defines the canonical scheduling contract. Its Pydantic models derive from `SchedulingBaseModel`, which is frozen, forbids extra fields and strips string whitespace. The solver receives domain data rather than TimeOffice rows or frontend file schemas.

## SchedulingDataset

One `SchedulingDataset` aggregates a `PlanningMonth` and tuples of planning units, plans, shifts, dated staffing requirements, employees, memberships, Sunday work history, wishes, assignments, availability, monthly accounts and objective weights. `TimeOfficeService.fetch_dataset` maps source rows and invokes `validate_scheduling_dataset` before returning it.

| Concept                     | Meaning and important fields                                                            |
| --------------------------- | --------------------------------------------------------------------------------------- |
| `PlanningMonth`             | Full calendar month identified by year and month                                        |
| `PlanningUnit`              | Positive ID, display name and type: station or shared pool                              |
| `PlanningUnitMembership`    | Employee/unit link with date validity, staffing level and home/replacement flags        |
| `Employee`                  | Stable ID, display name, professional/assistant/trainee staffing level and capabilities |
| `Shift`                     | ID/code/type, staffing role, start/end minutes of day and net work minutes              |
| `DemandRequirement`         | Positive required count for a specific unit, date, shift and staffing level             |
| `Plan`                      | Planning record associated with a unit and month                                        |
| `Assignment`                | Employee, date, shift, assignment type and applicable unit                              |
| `Availability`              | Hard unavailability, including supported date/shift restrictions                        |
| `Wish`                      | Desired work/free day or shift; distinct from hard restrictions                         |
| `MonthlyWorkAccount`        | Target and available actual working minutes for the employee                            |
| `EmployeeSundayWorkHistory` | Imported Sunday work context                                                            |
| `SolverObjectiveWeights`    | Per-unit values used by objective penalties                                             |

Work durations and accounts use minutes; dates use calendar dates. Shift clock minutes are in `[0, 1440)`, and overnight end times can be earlier than start times. Net work time is stored separately from elapsed clock time.

A `PLANNED` assignment belongs to a selected unit and requires its unit ID. `EXTERNAL` work blocks the person without satisfying selected-unit demand and omits its source unit ID. `GENERATED` assignments represent solver output. Membership intervals determine eligibility; a shared-pool type does not create membership automatically.

## Validation and output

Model validators check individual fields and relationships. `api/app/validation/` checks aggregate consistency across IDs, dates and entities. Solver-specific indexes and decision variables are derived later in `solver/cp_sat/`.

`Solution` in `api/app/solver/models.py` carries status, generated assignments, diagnostics and audit. The existing audit is implemented by solver components, not an independent acceptance checker. Canonical portable bundles and accepted CSV exports remain pending; the retired JSON file formats are not this domain contract.

For exact fields and validators, read the model modules rather than copying frontend legacy formats. [API schemas](api.md) describe HTTP DTOs; [TimeOffice](timeoffice.md) describes source translation.
