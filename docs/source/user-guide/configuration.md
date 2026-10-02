# Monthly configuration

The **Verfügbarkeit** and **Mindestbesetzung** pages edit the inputs of one planning month. The offline [browser procedure](../development/testing.md#staff-admin-browser-flows) passes against fictional SQL results, and saves against the prepared test database are recorded under [current limitations](../validation/index.md#webapp-integration).

Return to the [documentation overview](index.md).

## Availability and wishes

Choose the month and stations, then open **Verfügbarkeit**. Pick an employee of the selection, listed as `ID · Name` and sorted by name; the choice is kept in the URL (`employee=`). The list needs only names and memberships, so it works even when an employee's monthly account is still incomplete. The calendar shows three things per day:

- **Abwesenheit (TimeOffice)**: approved absences from the roster system, such as `Urlaub · U`. They are read-only here.
- **Einschränkung**: project availability. Choose _Nicht verfügbar_, _Urlaub_, _Fortbildung_, _Frei_ or _Nur bestimmte Schichten_ with the allowed shifts, plus an optional reason.
- **Wunsch**: a free day, a free shift, a preferred day or a preferred shift.

The first day of the month is open for editing; click another day to switch. Change the entry and press **Einschränkung speichern** or **Wunsch speichern**. **Einschränkung entfernen** and **Wunsch entfernen** delete only that day's entry. An employee has at most one availability entry and one wish per day; saving replaces it.

Generation considers wishes after gaps and health rules and before the monthly balance, spreading unavoidable denials fairly over employees; a wish never binds and always yields to an Einschränkung or absence. The page says so next to the wish form. The review shows what became of every wish; see [review](review.md#read-the-status-and-act-on-it).

## Dated staffing requirements

Open **Mindestbesetzung**. With several stations selected, a tab per station chooses the station (`station=` in the URL). The card _Tägliche Mindestbesetzung_ holds the whole editor: the qualification tabs **Fachkraft**, **Hilfskraft**, **Azubi** and **MFA**, the save controls, the weekly pattern and the dated grid with one row per date and one column per reference shift (F, Z, S, N). Weekends and North Rhine-Westphalia public holidays are shaded, and a holiday's name appears under its date. Enter whole numbers from 0 to 99; an empty or zero cell means nobody is required. Another value, such as `-1` or `1.5`, is kept and marked, and **Speichern** then fails with "Mindestbesetzung ungültig" until you correct it.

Edits stay unsaved until **Speichern**. Every cell whose value differs from the saved month has a thick amber border and bold digits, also when it was changed to zero; screen readers announce "Geändert, gespeichert: _n_" with the saved value, and pointing at the cell shows it. A qualification tab with changed cells carries a dot, and the toolbar counts the unsaved changes. A successful save or **Zurücksetzen** (which restores the last saved month) removes every mark; after a failed save the changes and their marks stay. On narrow screens the grid scrolls horizontally, and the save controls stay at the top of the card instead of following the scroll. Until a month has been saved once, the page says that no staffing demand is saved; afterwards a saved empty month means nobody is required.

To fill a month quickly, open **Wochenmuster anwenden**. Enter counts for Monday to Sunday and a holiday row for the shown qualification, then press **Vorschau**. Each qualification has its own pattern while the page is open. The backend applies the pattern to the month with its NRW calendar; public holidays take the holiday row. The preview lists the dates whose values change. **Übernehmen** replaces those dates in the unsaved grid and marks the changed cells like direct edits; **Verwerfen** keeps the grid as it was. Save afterwards to persist the result. The pattern itself is not stored and does not affect other months.

## Objective order

There are no weight settings. Generation optimizes gaps, health, station transfers, wishes, monthly accounts and intermediate duties strictly in this order, one after the other; see the [solver reference](../architecture/solver.md#objective). The order is fixed in code.

## Save scope and validation failures

- An availability or wish save changes only the named employee and date. Native absences, other days and other employees stay unchanged.
- A demand save replaces only the chosen station and month. Other months and stations stay unchanged.
- The API rejects invalid entries with `422` before writing: an employee without a membership in the month, a non-reference shift, _Nur bestimmte Schichten_ without shifts, shifts on another type, a demand date outside the month, a duplicate cell, a count that is not a whole number from 1 to 99 (0 to 99 in a pattern), or a jumper pool or a station without a target plan. The pattern preview checks the station and shifts the same way.
- If a save fails, the page shows the error and "nicht gespeichert". Your input and unsaved changes stay on screen; no success message appears.
- Connected use needs the [project tables](../architecture/timeoffice.md#project-tables) and write permission on them. Without them both these pages and the **Mitarbeiter** inspection fail with a TimeOffice error, because inspection also reads project availability.
