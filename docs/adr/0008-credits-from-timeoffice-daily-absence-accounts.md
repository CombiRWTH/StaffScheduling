# Read work credits from TimeOffice's daily absence accounts

An employee's dated credits (hours counted towards the monthly target without being worked, such as vacation or school days) come from TimeOffice's daily absence-hour accounts in `TPersonalKontenJeTag`: vacation, internal and external training, and school. `read_accounts` returns each `MonthlyWorkAccount` with these credits. Every credit row must fall on a roster absence of its code. A credited absence on a Monday-to-Friday date that is not an NRW public holiday must have its booking, because TimeOffice books those days and no others.

## Considered Options

- **A project table of monthly credit declarations** (`StaffSchedulingEmployeeMonthEvidence`, the earlier design). Rejected: TimeOffice already stores the same facts per date, so the table duplicated them, needed manual preparation for every employee and month, and could drift from the roster.
- **Credits derived from the absence days times contract hours.** Rejected: it would invent a crediting rule inside the adapter instead of reading what TimeOffice booked.
- **Monthly absence accounts** (the monthly sums of the same accounts). Rejected: they are not dated, but the scheduling rules need the date of each credit.

## Consequences

The project tables shrink to availability, wishes and demand. A missing booking on a weekday stops the inspection instead of crediting zero. Employees who work fewer than five days a week would need a different booking rule; they currently fail this check rather than being credited wrongly. A replacement database must supply dated credits in the same canonical form.
