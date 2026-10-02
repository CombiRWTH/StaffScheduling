# Publish marked duties into TimeOffice target plans

Publication writes the accepted schedule under review into TimeOffice's own roster table, `TPlanPersonalKommtGeht`, in the selected stations' target plans: one row per work segment of the reference shift, the way TimeOffice stores worked duties. Each row carries `Info` = `StaffScheduling`. These marked worked rows are the application's whole output: publishing replaces them and clearing removes them, while absences, native wishes, duties entered in TimeOffice and every other plan stay. Everything is validated before the old rows are deleted, in one serializable transaction that reads the new rows back before committing. A duty entered in TimeOffice or an absence on a duty's date blocks the publication instead of being overwritten.

## Considered Options

- **A separate project table of published schedules.** Rejected: planners work in TimeOffice, and a schedule that only exists beside it is not published. The adapter already reads this table, so writing it keeps one source of truth.
- **Treat every worked row of a target plan as output.** Rejected: it would delete duties planners entered by hand in the same plan, which the generation never read and the publication never wrote.
- **Separate plans or row statuses per generation.** Rejected: TimeOffice's roster key `(RefPersonal, Datum, RefStati, lfdNr)` excludes the plan, so another plan does not avoid key collisions, and the prepared targets are the plans reads already select.

## Consequences

This is the adapter's first write into the schema TimeOffice owns, so it needs SELECT, INSERT and DELETE on `TPlanPersonalKommtGeht`. The `Info` text is visible in TimeOffice and must not be reused by planners; changing the marker strands rows published with the old one. No `TPlanPersonal` rows are written, and the TimeOffice client's display of published duties is unverified. Collisions with concurrent writers fail and roll back (`409 concurrent`); the API must still run as one process for its publication lock. A replacement database implements `publish` and `clear` with the same canonical meaning.
