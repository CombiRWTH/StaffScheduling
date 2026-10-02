# Review, import and export

**Dienstplan → Prüfen** shows the latest schedule — generated or imported — with its independent check, the duties, staffing and monthly accounts, and offers publication, downloads and import. Nothing is saved, and nothing is published until you [publish it explicitly](publication.md); the schedule is kept only until the API restarts. The procedure below is checked with controlled browser flows and fictional data and with a live January run on the prepared test database; see [current limitations](../validation/index.md#review-import-and-export).

Return to the [documentation overview](index.md).

## Read the status and act on it

After a generation that found a schedule, _Letzte Generierung_ on **Erstellen** links to **Dienstplan prüfen** with the job's month and stations. A generation without a schedule (infeasible, no result in time, failed) leaves the previous schedule under review.

The page always reviews one schedule, from top to bottom: its summary with the actions, the duty grid and the monthly accounts. The card _Dienstplan zur Prüfung_ names the month and stations, whether the schedule was generated or imported and when, and its number of duties. One status line says whether it may be used:

- **Regeln eingehalten · Kann veröffentlicht werden**: the independent check accepted it.
- **Regelverstöße**: the schedule breaks a rule and is not usable. A box below lists every finding with its rule, message, employee, date and station.
- **Unvollständig geprüft**: a check promised for the month lacked input; the box lists the missing inputs with their dates.

Only an accepted schedule is usable; any other one is a diagnosis. The check, not the solver, decides.

Next to the status sit the actions: **In TimeOffice veröffentlichen** (only for an accepted schedule; see [publication](publication.md)), **Herunterladen**, **Importieren** and **Veröffentlichte Dienste entfernen**. Each opens a small panel; nothing changes until you confirm there.

If the header selection is another month or other stations, the page says so instead of showing the schedule as the selected one; **Zu diesem Umfang wechseln** selects the schedule's own scope. Without a schedule, the card offers import and removal only.

The collapsed section **Technische Details** is for diagnosing a run, not needed to use the schedule: the solver status, the **Optimalitätslücke** (the relative gap to CP-SAT's proven bound; a large gap means a weak bound, not a broken rule and not missing staff), run time and limit, search threads, random seed, the derived objective weights (health · accounts · intermediate duties), objective value and bound, the check's scores (health events from six-day runs and backward shift changes, total account deviation, surplus intermediate duties), obligations beyond the month that cannot be assessed here (the next month's start, annual free Sundays) and any solver diagnostics.

## Inspect employee and unit schedules

The card _Dienstplan_ lists every participating employee by date — ID, name and every home unit of the month — also employees without duties. A duty shows only its shift code in the shift colour (Früh, Zwischen, Spät, Nacht): the employee column already names where they belong. Pointing at a duty shows station, shift and times, credited qualification and origin, and screen readers read the same text.

Only a duty worked outside its origin — the employee's home station or jumper pool _on that date_, as the backend dates it — is highlighted as a transfer by a dashed border. With more than one station selected, a transfer also names the station where it is worked by a short code (a short name as is, a longer one by its initials, for example _ESN_); the legend lists the codes. A duty whose employee has no dated home is tagged **?** (_Herkunft unbekannt_); the check reports it as an eligibility finding. The comparison never uses the row's home units, so a home change within the month is shown per date. Absences and restrictions show their reason (for example `U`, `SC`); weekends and public holidays are shaded; a red frame marks an employee and date with a finding. Below, **Besetzung** gives for each station and shift the assigned against the required staff per date, red when short; pointing at a number splits it by qualification.

Search by name or ID, or open **Vollbild** (leave with the button or Esc). The legend under the table explains the marks. On narrow screens the grid scrolls horizontally; the employee column stays in place.

_Monatskonten_ lists every employee's target, credited, generated minutes and balance (generated + credited − target) as the backend computed them; a balance outside the allowed band is marked when the check reports it.

## Import and validate a portable bundle

1. Select **Importieren** and choose an `input.json` and its `result.json`.
2. Select **Dateien importieren**.

The backend validates the pair before replacing the schedule under review: both files must be format version 1 without unknown fields, `result.json` must name the SHA-256 digest of exactly this `input.json` and its month, contain a found schedule whose assignments reference the input's employees, stations and shifts within the month, have been solved with the current rule settings, and carry a schedule check equal to an independent re-check. A rejected pair shows why in the panel (invalid files, files that do not belong together, no schedule, other rule settings, unknown duties, a differing check) and _Der bisherige Dienstplan bleibt zur Prüfung_: the current review and its downloads stay unchanged. A valid pair closes the panel and replaces the review. An import never publishes and never stores a copy.

## Download JSON and CSV files

**Herunterladen** lists the four files of the schedule under review: `input.json`, `result.json`, `schedule.csv` and `employees.csv`. Their fields are described under [examples and reproduction](../validation/examples.md#bundle-files). The files need no saved schedule library and can be read, re-solved and checked without TimeOffice. For a schedule that is not accepted, the list states that the files are a diagnosis, not a usable schedule.
