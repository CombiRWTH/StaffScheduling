# Review, import and export

**Dienstplan → Prüfen** shows the latest schedule, generated or imported. You see its independent check, the duties, the staffing and the monthly accounts. From here you publish, download or import. Nothing is saved, and nothing reaches TimeOffice until you [publish it explicitly](publication.md). The schedule is kept only until the API restarts. See [current limitations](../validation/index.md#review-import-and-export) for what has been checked.

Return to the [documentation overview](index.md).

## Read the status and act on it

After a generation that found a schedule, _Letzte Generierung_ on **Erstellen** links to **Dienstplan prüfen** with the job's month and stations. A generation without a schedule (infeasible, no result in time, failed) leaves the previous schedule under review.

The page always reviews one schedule. From top to bottom it shows:

- the summary with the actions;
- the wishes (collapsed);
- the duty grid;
- the monthly accounts (collapsed).

Select a collapsed title to open it. The summary card is headed with the month and stations. It says whether the schedule was generated or imported, when, and how many duties it has. One status line says whether it may be used:

- **Regeln eingehalten · Kann veröffentlicht werden**: the independent check accepted it. With gaps, the line adds _Lücken werden nicht veröffentlicht_.
- **Regelverstöße**: the schedule breaks a rule and is not usable. A box below lists every finding with its rule, message, employee, date and station.
- **Unvollständig geprüft**: a check promised for the month lacked input. The box lists the missing inputs with their dates.

Only an accepted schedule is usable; any other one is a diagnosis. The check decides, not the solver.

When required slots stay unfilled, an amber box **Lücken** follows, headed _n unbesetzte Pflichtstellen_. It has one line per station, date, shift and qualification, with the missing and the required staff. The grid's **Besetzung** rows mark the same slots. No eligible employee was free for them, so request guest staff for these shifts. Gaps are never published as duties. The check accepts a schedule only if every shortfall is listed exactly.

When the month has wishes, the collapsed card **Wünsche** follows the summary. Its title counts the outcomes: _erfüllt_, _nicht erfüllt_ and _nicht erfüllbar_. Opened, it lists every wish by date with employee, wish and outcome. Wishes never bind.

- _Nicht erfüllbar_: the inputs of the wish's own day rule it out. Examples are an availability entry, a missing membership, the shift's own work rules, or a trusted duty touching a wished free day. Such a wish does not count against the schedule.
- _Nicht erfüllt_: only rules across days prevent it, such as the rest after a trusted night.

The actions sit next to the status. Each opens a small panel:

- **In TimeOffice veröffentlichen**, only for an accepted schedule; see [publication](publication.md).
- **Herunterladen** lists the files.
- **Importieren** replaces the review only after **Dateien importieren** and a successful validation.
- **Veröffentlichte Dienste entfernen**.

Publishing and removal change TimeOffice only after their confirmation button.

The header selection may name another month or other stations. Then the page says so instead of showing the schedule as the selected one. **Zu diesem Umfang wechseln** selects the schedule's own scope. Without a schedule, the card offers import and removal only.

The collapsed section **Technische Details** helps to diagnose a run; you do not need it to use the schedule. It shows:

- the solver status, run time and limit, search threads and random seed;
- one line per objective stage in solving order, from **Stufe 1: Lücken** to **Stufe 6: Überzählige Zwischendienste**, with its value and either _optimal_ or its proven bound (_Schranke_; a weak bound is not a broken rule);
- the check's scores: gaps, health events (six-day runs, backward shift changes, isolated workdays, back-to-back worked weekends), station transfers, the wish cost, total account deviation and surplus intermediate duties;
- obligations beyond the month that cannot be assessed here, such as the next month's start and annual free Sundays;
- any solver diagnostics with their code and English message.

## Inspect employee and unit schedules

The card _Dienstplan_ lists every participating employee by date, including employees without duties. The employee column shows ID, name and every home unit of the month, each on one line. A long name is cut and shown in full on pointing.

A duty shows only its shift code in the shift colour (Früh, Zwischen, Spät, Nacht). The employee column already says where they belong. Pointing at a duty shows station, shift, times, credited qualification and origin. Screen readers read the same text.

Origin is the employee's home station or jumper pool _on that date_, as the backend dates it. The grid marks:

- Transfers: a duty worked outside its origin has a dashed border. With more than one station selected, it also names the station where it is worked by a short code. A short name stays as it is; a longer one becomes its initials, for example _ESN_. If two codes would be the same, full names are used. The legend lists the codes.
- **?** (_Herkunft unbekannt_): the duty's employee has no dated home. The check reports it as an eligibility finding.
- Absences: native TimeOffice absences show their code, for example `U` or `SC`.
- Availability: project entries show their short code with the reason on pointing: `–` not available, `U` vacation, `FB` training, `Fr` free, `nur` only certain shifts.
- Findings: a red frame marks an employee and date with a finding.

Weekends and public holidays are shaded. The comparison never uses the row's home units, so a home change within the month is shown per date.

Below, **Besetzung** shows the filled against the required slots per station, shift and date. Each qualification counts only up to its own demand. Another qualification never fills it, and a surplus never covers another's gap. Where nothing is required, the row shows the assigned staff against `0`. A gap cell is tinted red and shows the missing staff under the count, for example `1/2` over `−1`. Pointing at a number names the missing qualification. It also lists assigned against required staff per qualification, surplus included.

Search by name or ID, or open **Vollbild** (leave with the button or Esc). The legend under the table explains only the marks this schedule shows. On narrow screens the grid scrolls horizontally, and the employee column stays in place.

_Monatskonten_ is collapsed and titled with the number of employees. It lists every employee's **Soll**, **Gutschriften**, **Geplant** and **Saldo** (Geplant + Gutschriften − Soll) in hours and minutes. The values are the backend's. A balance outside the allowed band is marked when the check reports it.

## Import and validate a portable bundle

1. Select **Importieren** and choose an `input.json` and its `result.json`.
2. Select **Dateien importieren**.

The backend validates the pair before it replaces the schedule under review. Both files must be format version 2 without unknown fields. `result.json` must also:

- name the SHA-256 digest of exactly this `input.json` and its month;
- contain a found schedule whose assignments and gaps reference the input's employees, stations and shifts within the month;
- have been solved with the current rule settings;
- carry a schedule check equal to an independent re-check.

A rejected pair shows the reason in the panel: invalid files, files that do not belong together, no schedule, other rule settings, unknown duties or a differing check. The panel adds _Der bisherige Dienstplan bleibt zur Prüfung_; the current review and its downloads stay unchanged. A valid pair closes the panel and replaces the review. An import never publishes and never stores a copy.

## Download JSON and CSV files

**Herunterladen** lists the five files of the schedule under review: `input.json`, `result.json`, `schedule.csv`, `employees.csv` and `gaps.csv`. [Examples and reproduction](../validation/examples.md#bundle-files) describes their fields. The files need no saved schedule library. You can read, re-solve and check them without TimeOffice. For a schedule that is not accepted, the list states that the files are a diagnosis, not a usable schedule.
