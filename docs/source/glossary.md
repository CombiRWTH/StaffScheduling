# Glossary

Monthly shift planning for hospital stations and their jumper pools: inspecting who can be planned, generating a schedule and publishing it to the hospital's roster system. German labels are the terms shown in the webapp.

## Planning scope

**Planning month**:
One full calendar month; every plan, account, availability entry and staffing demand is scoped to exactly one.
_Avoid_: period, interval, case

**Planning unit**:
An organisational unit employees belong to: either a station or a jumper pool. Every planning unit is a pool of employees; only its type decides whether it is planned.
_Avoid_: unit of work, case, department

**Station** (Station):
A planning unit with its own staffing demand that receives assignments.
_Avoid_: ward, case, destination unit

**Jumper pool** (Springerpool):
A planning unit whose employees are based there and stand in at stations. By definition it has no staffing demand and receives no assignments; its employees are assigned at stations where they hold a replacement membership.
_Avoid_: shared pool, pool (on its own), float team

**Planning selection** (Planungsauswahl):
The planning month together with the chosen stations; every view works on one selection.
_Avoid_: scope, filter, case

**Associated jumper pool** (Zugehöriger Springerpool):
A jumper pool that at least one member of a selected station has as home unit; its employees join the inspection without becoming eligible for the stations.
_Avoid_: linked jumper pool

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
Whether an employee may be planned at a station on a date, given by a membership there; a jumper pool home alone grants none.
_Avoid_: access, permission

## Monthly facts

**Monthly account** (Monatskonto):
An employee's target and actual working minutes for the planning month.
_Avoid_: hour bank, balance

**Work credit** (Gutschrift):
Dated minutes counted towards the target without being worked, such as approved absence or trusted work. TimeOffice books absence credits per date in its daily absence-hour accounts.
_Avoid_: bonus, adjustment

**Availability** (Verfügbarkeit; one entry: Einschränkung):
A date on which an employee must not be planned, or may only be planned for certain shifts. It always binds planning.
_Avoid_: constraint (a solver rule), hard restriction, blocker

**Native absence** (Abwesenheit):
An approved absence read from the roster system, such as vacation; shown next to availability but never edited by this application.
_Avoid_: availability entry, blocker

**Wish** (Wunsch):
An employee's soft preference for a free day or shift, or for working a day or shift, on one date at any station; generation considers it and never binds to it.
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
An employee working a specific shift on a specific date at a station, credited as one qualification.
_Avoid_: membership, Zuordnung

**Credited qualification**:
The qualification an assignment counts as towards staffing demand; it comes from the employee's membership at that station on that date.
_Avoid_: role, employee level (when the membership differs)

**Trusted context** (Kontext):
Duties around a planning month from approved context plans, with the dates they cover completely; they constrain the month's boundary rules but never count towards its demand or accounts.
_Avoid_: history, previous plan, fixed assignments

**Coverage** (Besetzung):
Required against assigned staff of a station, date, shift and qualification, with the missing count; also where nobody is required but someone is assigned. A duty counts as its credited qualification.
_Avoid_: staffing level, fill rate

**Gap** (Lücke):
An unfilled required slot of a station, date, shift and qualification; reported separately from the assignments so guest staff can be requested, and never published as a duty.
_Avoid_: shortage draft, placeholder, hidden employee, optimality gap

**Generation** (Generierung):
One solver run over the full month of a planning selection; it yields at most a generated candidate and is kept only until the API restarts.
_Avoid_: solve job, case, optimization

**Generated candidate** (Entwurf):
A schedule produced by the solver that has not yet passed independent acceptance.
_Avoid_: solution, result (when meaning an accepted schedule)

**Schedule check** (Prüfung):
The independent evaluation of a schedule's assignments against every hard rule, separate from the solver status; it accepts, rejects or reports the schedule as incomplete and lists what it could not assess.
_Avoid_: audit, validation (when meaning input validation)

**Accepted schedule**:
A generated candidate that passed the schedule check with no violation and no missing promised input; it may contain gaps.
_Avoid_: optimal schedule, final plan

**Schedule under review** (Dienstplan zur Prüfung):
The latest generated or validly imported schedule that the review shows and offers for download; kept only until the API restarts, never saved or published by that.
_Avoid_: saved schedule, library entry

**Portable bundle**:
The six files of one monthly run: `input.json`, `result.json` paired to it by the SHA-256 digest of its bytes, and the derived `schedule.csv`, `employees.csv`, `besetzung.csv` and `gaps.csv`; readable and checkable without TimeOffice.
_Avoid_: case, export folder, legacy JSON

**Origin** (Herkunft):
The employee's home station or jumper pool on a duty's date, as opposed to the station where the duty is worked.
_Avoid_: source unit, pool (alone)

**Transfer** (Einsatz außerhalb der Herkunft):
A duty worked at a station other than its origin on that date. A home change within the month changes the origin from its first date on.
_Avoid_: loan, external duty

**Station transfer** (Einsatz anderer Station):
A duty worked at another station by an employee whose origin on that date is a station, through a replacement membership; duties of jumper-pool employees never count.
_Avoid_: jumping, Ersatzeinsatz

**Published schedule**:
An accepted schedule written to the roster system for its stations and month.
_Avoid_: exported schedule, inserted plan
