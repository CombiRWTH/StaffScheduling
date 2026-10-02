# Store monthly configuration in project tables, not in TimeOffice roster rows

Monthly availability, wishes and dated staffing demand are edited in the webapp and saved in four small project tables next to the TimeOffice schema (`api/sql/supplemental-tables.sql`). Each write replaces exactly one key, an employee date or a station month, inside one transaction. Approved absences stay in TimeOffice and are only read.

## Considered Options

- **Native TimeOffice wish/absence rows** (`TPlanPersonalKommtGeht` with `Wunschdienst`, as the imported code did). Rejected: a row needs a plan, profession and sequence number. The old writer guessed these from existing roster rows, so it failed on empty target plans and its deletes could reach unrelated entries.
- **The recurring weekday table `StaffSchedulingMinimalStaffing`.** Rejected: it stored one weekday pattern per station, so a month edit silently changed every month, and it could not hold MFA or a holiday.
- **A JSON column on the monthly evidence row.** Rejected: every single-day edit would rewrite a whole month, and a row would have to exist before anything could be saved.

## Consequences

TimeOffice users do not see project availability or wishes, and native TimeOffice wishes are not read. A replacement database must supply the same canonical reads and scoped writes. Demand declares a saved month explicitly, so "never configured" is distinct from "nobody required".
