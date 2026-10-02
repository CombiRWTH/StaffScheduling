# Review, import and export

**Dienstplan → Prüfen** shows the latest schedule — generated or imported — with the solver result, the independent schedule check, the duties, staffing and monthly accounts, and offers its files for download. Nothing is saved, and nothing is published until you [publish it explicitly](publication.md); the schedule is kept only until the API restarts. The procedure below is checked with controlled browser flows and fictional data and with a live January run on the prepared test database; see [current limitations](../validation/index.md#review-import-and-export).

Return to the [documentation overview](index.md).

## Read solution status and independent acceptance

After a generation that found a schedule, _Letzte Generierung_ on **Erstellen** links to **Dienstplan prüfen** with the job's month and stations. A generation without a schedule (infeasible, no result in time, failed) leaves the previous schedule under review.

The page always reviews one schedule. Its card _Dienstplan zur Prüfung_ names the month, the stations and whether it was generated or imported, and when. If the header selection is another month or other stations, the page says so instead of showing the schedule as the selected one; **Zu diesem Umfang wechseln** selects the schedule's own scope.

| Part              | What it shows                                                                                                                                                                                        |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Solver-Status     | What CP-SAT found: **Optimale Lösung** or **Lösung gefunden** (time limit ended the search)                                                                                                          |
| Prüfung           | The independent check: **Regeln eingehalten** (accepted), **Regelverstöße** (rejected) or **Unvollständig geprüft** (a promised check lacked input)                                                  |
| Optimalitätslücke | The relative gap between the objective value and CP-SAT's proven bound; a large gap means a weak bound, not a broken rule and not missing staff (see _Besetzung_ below)                              |
| Bewertung         | The check's scores: health events (six-day runs and backward shift changes), total deviation of the monthly accounts in minutes, surplus intermediate duties, and the number of duties               |
| Verstöße          | Every finding of the check with its rule, message, employee, date and station                                                                                                                        |
| Nicht bewertet    | Rules the input cannot decide, with their date window: _fehlende Eingaben, verhindert die Annahme_ blocks acceptance; _über den Monat hinaus_ (the next month's start, annual free Sundays) does not |

Only an accepted schedule is usable; any other one is a diagnosis. The check message, not the solver status, decides.

The collapsed section **Solver-Details** holds the run's actual time and time limit, search threads, random seed, the derived objective weights (health · accounts · intermediate duties), the objective value and the proven bound. Solver diagnostics, findings and items not assessed always stay visible.

## Inspect employee and unit schedules

The card _Dienstplan_ lists every participating employee (ID, name and home unit) by date, also employees without duties. A duty shows its shift code in the shift colour (Früh, Zwischen, Spät, Nacht) and, with more than one station, the station where it is worked; pointing at it shows station, shift and times, credited qualification and origin. Absences and restrictions show their reason (for example `U`, `SC`); weekends and public holidays are shaded; a red frame marks an employee and date with a finding. Below, **Besetzung** gives for each station and shift the assigned against the required staff per date, red when short; pointing at a number splits it by qualification.

Search by name or ID, switch to **Kompakt** for narrower columns, or open **Vollbild** (leave with the button or Esc). The legend under the table explains the marks.

_Monatskonten_ lists every employee's target, credited, generated minutes and balance (generated + credited − target) as the backend computed them; a balance outside the allowed band is marked when the check reports it.

## Import and validate a portable bundle

1. Under **Importieren**, choose an `input.json` and its `result.json`.
2. Select **Importieren**.

The backend validates the pair before replacing the schedule under review: both files must be format version 1 without unknown fields, `result.json` must name the SHA-256 digest of exactly this `input.json` and its month, contain a found schedule whose assignments reference the input's employees, stations and shifts within the month, have been solved with the current rule settings, and carry a schedule check equal to an independent re-check. A rejected pair shows why (invalid files, files that do not belong together, no schedule, other rule settings, unknown duties, a differing check) and _Der bisherige Dienstplan bleibt zur Prüfung_: the current review and its downloads stay unchanged. An import never publishes and never stores a copy.

## Download JSON and CSV files

The four buttons download the schedule under review: `input.json`, `result.json`, `schedule.csv` and `employees.csv`. Their fields are described under [examples and reproduction](../validation/examples.md#bundle-files). The files need no saved schedule library and can be read, re-solved and checked without TimeOffice. Under a schedule that is not accepted, the page states that the files are a diagnosis, not a usable schedule.
