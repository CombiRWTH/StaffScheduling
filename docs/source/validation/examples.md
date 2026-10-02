# Examples and reproduction

For readers trying to inspect or reproduce the example schedules. The prepared TimeOffice inputs below exist; how they were checked is recorded under [current limitations](index.md#webapp-integration). No accepted example bundle is supplied yet, and the run-without-TimeOffice and validation sections are still outlines; see [current limitations](index.md) and the [documentation guide](../development/documentation.md).

Return to the [documentation overview](../index.md).

## Example scope and file inventory

Two fictional stations and one jumper pool, planned together for each month from January to June 2026: twelve station months. Station `BSP-A` uses demand profile 85 and `BSP-B` profile 79 of the chair's minimum-staffing table; the profile numbers are labels, not database keys. The TimeOffice units and their keys are listed in the [adapter reference](../architecture/timeoffice.md#prepared-example-units). Exported files are not yet part of the repository.

## Input data and boundary context

All people, contracts and absences are invented for the example, all of them adults. Names follow the pattern `Beispiel A Anna` (surname = home unit) and staff numbers `BSP-A-P01` (P professional, H assistant, AZ trainee, MFA medical assistant).

| Home unit  | Professional | Assistant | Trainee | MFA |
| ---------- | ------------ | --------- | ------- | --- |
| `BSP-A`    | 9            | 4         | 6       | 3   |
| `BSP-B`    | 13           | 6         | 6       | 3   |
| `BSP-JUMP` | 5            | 2         | –       | –   |

- **Contracts.** Full time is 39 hours a week; some staff work 29.25 or 19.5 hours. The monthly target is the weekly hours ÷ 5 for each Monday–Friday that is not an NRW public holiday. Holiday-rich months therefore have lower targets but the same demand.
- **Eligibility.** Station staff are members of their station only. Jumper pool staff have the jumper pool as home and replacement memberships at both stations. Memberships run from 2025-12-01 to 2026-07-31, which covers the boundary context.
- **Absences.** Everyone has three five-workday vacation blocks (`U`) spread over the half year. Each trainee also has one school week (`SC`) per month outside their vacation. Each absence workday is credited with the weekly hours ÷ 5 in TimeOffice's daily accounts.
- **Demand.** Saved per station month from the profile's weekday and weekend/holiday rows (NRW holidays take the weekend row). Professional, assistant, trainee and MFA demand stay separate.
- **Capacity.** Per qualification and month, target minus credits exceeds demand hours by 4–60 % (May is tightest: assistants 1.04, professionals 1.07). This is an hours check only; it does not show that a schedule satisfying every rule exists.
- **Boundary context.** Fictional worked duties for 2025-12-18 to 2025-12-31 and 2026-07-01 to 2026-07-07 respect one duty per day, no early shift after a late shift, no day shift directly after a night, at most three nights in a row followed by two free days, and at most five consecutive working days; the shortest rest between duties is 14 hours. They meet the stations' demand on every context day. These properties were checked on the duties read back from the database, separately from the code that produced them. Generation reads this context as trusted duties around the month. Three professionals' July 3 nights were removed afterwards, because with them no professional could work the June 30 night within the night and recovery rules.
- **Not included.** Wishes, special capabilities and history before 2025-12-18. Checks that need a longer history, such as 24-week averaging, cannot be assessed from this data.

## Run without TimeOffice

## Validate monthly and sequence results

## Interpret objectives and solver settings
