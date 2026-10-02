# Staff scheduling

Monthly shift planning for hospital stations and their shared pool: inspecting who can be planned, generating a schedule and publishing it to the hospital's roster system. German labels are the terms shown in the webapp.

## Planning scope

**Planning month**:
One full calendar month; every plan, account, availability entry and staffing demand is scoped to exactly one.
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
The prepared statement that an employee's work credits for a month are complete, with its source.
_Avoid_: proof file, attestation

**Availability** (Verfügbarkeit; one entry: Einschränkung):
A date on which an employee must not be planned, or may only be planned for certain shifts. It always binds planning.
_Avoid_: constraint (a solver rule), hard restriction, blocker

**Native absence** (Abwesenheit):
An approved absence read from the roster system, such as vacation; shown next to availability but never edited by this application.
_Avoid_: availability entry, blocker

**Wish** (Wunsch):
A soft preference for a shift or free day; stored and shown, but not yet considered when generating a schedule.
_Avoid_: request, preference rule, availability

**Employee inspection** (Mitarbeiterprüfung):
The read-only, all-or-nothing check of every employee in a planning selection and their monthly facts.
_Avoid_: employee list, import

## Schedules

**Staffing demand** (Mindestbesetzung):
The minimum number of employees per qualification required for a station, date and shift. It is saved per station month; within a saved month a missing entry requires nobody.
_Avoid_: target staffing, capacity

**Weekly pattern** (Wochenmuster):
Counts per weekday plus a public-holiday row that fill one month's staffing demand once; it is not stored or carried into other months.
_Avoid_: template, recurring demand

**Public holiday** (Feiertag):
A North Rhine-Westphalia public holiday; it keeps its weekday but takes the holiday row of a weekly pattern.
_Avoid_: weekend day

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
