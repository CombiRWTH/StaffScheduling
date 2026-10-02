# Staff scheduling

Monthly shift planning for hospital stations and their shared pool: inspecting who can be planned, generating a schedule and publishing it to the hospital's roster system. German labels are the terms shown in the webapp.

## Planning scope

**Planning month**:
One full calendar month; every plan, account and constraint is scoped to exactly one.
_Avoid_: period, interval, case

**Planning unit**:
An organisational unit employees belong to: either a station or a shared pool.
_Avoid_: unit of work, case, department

**Station** (Station):
A planning unit with its own staffing demand that a schedule is generated for.
_Avoid_: ward, case, destination unit

**Shared pool** (Pool):
A planning unit of employees who are based there and stand in at stations; it has no staffing demand of its own.
_Avoid_: jumper pool, Springer, float team

**Planning selection** (Planungsauswahl):
The planning month together with the chosen stations; every view works on one selection.
_Avoid_: scope, filter, case

**Associated pool** (Zugehöriger Pool):
A shared pool that at least one member of a selected station has as home unit; its employees join the inspection without becoming eligible for the stations.
_Avoid_: linked pool

## People and memberships

**Employee** (Mitarbeiter):
A person identified by a stable ID that survives name changes.
_Avoid_: staff member record, worker

**Qualification** (Qualifikation):
The staffing category an employee counts as: Fachkraft, Hilfskraft, Azubi or MFA. MFA is distinct and never counts as Hilfskraft.
_Avoid_: role, level, profession

**Membership** (Zuordnung):
A dated link between an employee and a planning unit, carrying the qualification held there.
_Avoid_: assignment (that is a shift), mapping

**Home unit** (Heimat):
The one planning unit an employee originates from on a given day.
_Avoid_: primary unit, base station

**Replacement membership** (Ersatz):
A membership that lets an employee stand in at a unit that is not their home unit.
_Avoid_: secondary membership, jumper assignment

**Eligibility**:
Whether an employee may be planned at a station on a date, given by a membership there; a pool home alone grants none.
_Avoid_: access, permission

## Monthly facts

**Monthly account** (Monatskonto):
An employee's target and actual working minutes for the planning month.
_Avoid_: hour bank, balance

**Work credit** (Gutschrift):
Dated minutes counted towards the target without being worked, such as approved absence or trusted work.
_Avoid_: bonus, adjustment

**Evidence declaration** (Monatsnachweis):
The prepared statement that an employee's credits and additional constraints for a month are complete, with its source.
_Avoid_: proof file, attestation

**Constraint** (Einschränkung):
A date on which an employee must not be planned, or may only be planned for certain shifts.
_Avoid_: hard restriction, availability, blocker, absence (when meaning the constraint itself)

**Wish** (Wunsch):
A soft preference for a shift or free day that planning should try to honour.
_Avoid_: request, preference rule

**Availability** (Verfügbarkeit):
Umbrella for an employee's wishes and constraints in a month.
_Avoid_: using it for constraints alone

**Employee inspection** (Mitarbeiterprüfung):
The read-only, all-or-nothing check of every employee in a planning selection and their monthly facts.
_Avoid_: employee list, import

## Schedules

**Staffing demand** (Mindestbesetzung):
The minimum number of employees per qualification required for a station, date and shift.
_Avoid_: target staffing, capacity

**Shift** (Dienst):
A named working period of a day, such as early, late, night or intermediate.
_Avoid_: slot, duty block

**Assignment**:
An employee working a specific shift on a specific date.
_Avoid_: membership, Zuordnung

**Generated candidate**:
A schedule produced by the solver that has not yet passed independent acceptance.
_Avoid_: solution, result (when meaning an accepted schedule)

**Accepted schedule**:
A generated candidate that passed the independent acceptance check.
_Avoid_: optimal schedule, final plan

**Published schedule**:
An accepted schedule written to the roster system for its stations and month.
_Avoid_: exported schedule, inserted plan
