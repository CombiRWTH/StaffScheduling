# Monthly configuration

The **Verfügbarkeit** and **Mindestbesetzung** pages edit the inputs of one planning month. The offline [browser procedure](../development/testing.md#staff-admin-browser-flows) passes against fictional SQL results. No connected TimeOffice save has been verified yet; see [current limitations](../validation/index.md).

Return to the [documentation overview](index.md).

## Availability and wishes

Choose the month and stations, then open **Verfügbarkeit**. Pick an employee of the selection; the choice is kept in the URL (`employee=`). The calendar shows three things per day:

- **Abwesenheit (TimeOffice)**: approved absences from the roster system, such as `Urlaub · U`. They are read-only here.
- **Einschränkung**: project availability. Choose _Nicht verfügbar_, _Urlaub_, _Fortbildung_, _Frei_ or _Nur bestimmte Schichten_ with the allowed shifts, plus an optional reason.
- **Wunsch**: a free day, a free shift, a preferred day or a preferred shift.

Click a day, change the entry and press **Einschränkung speichern** or **Wunsch speichern**. **Einschränkung entfernen** and **Wunsch entfernen** delete only that day's entry. An employee has at most one availability entry and one wish per day; saving replaces it.

Wishes are saved and shown, but generation does not consider them yet. The page says so next to the wish form. The final examples contain no wishes.

## Dated staffing requirements

Open **Mindestbesetzung**. With several stations selected, a tab per station chooses the station (`station=` in the URL). Tabs for **Fachkraft**, **Hilfskraft**, **Azubi** and **MFA** show one row per date and one column per reference shift (F, Z, S, N). Weekends and North Rhine-Westphalia public holidays are shaded; holidays show their name. An empty or zero cell means nobody is required.

Edits stay unsaved until **Speichern**. **Zurücksetzen** discards them and restores the last saved month. Until a month has been saved once, the page says that no staffing demand is saved; afterwards a saved empty month means nobody is required.

To fill a month quickly, open **Wochenmuster anwenden**. Enter counts for Monday to Sunday and a holiday row for the shown qualification, then press **Vorschau**. The backend applies the pattern to the month with its NRW calendar; public holidays take the holiday row. The preview lists the dates whose values change. **Übernehmen** replaces those dates in the unsaved grid; **Verwerfen** keeps the grid as it was. Save afterwards to persist the result. The pattern itself is not stored and does not affect other months.

## Objective weights

There are no weight settings. The previously stored but ignored objective weights were removed; optimization controls are omitted until they work. Solver settings arrive with generation.

## Save scope and validation failures

- An availability or wish save changes only the named employee and date. Native absences, other days and other employees stay unchanged.
- A demand save replaces only the chosen station and month. Other months and stations stay unchanged.
- The API rejects invalid entries with `422` before writing: an employee without a membership in the month, a non-reference shift, _Nur bestimmte Schichten_ without shifts, shifts on another type, a demand date outside the month, a duplicate cell, a count below one, or a pool or a station without a target plan.
- If a save fails, the page shows the error and "nicht gespeichert". Your input and unsaved changes stay on screen; no success message appears.
- A connected save needs the [project tables](../architecture/timeoffice.md#project-tables) and write permission on them. Without them the save fails with a TimeOffice error.
