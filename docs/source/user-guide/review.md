# Review, import and export

**Dienstplan → Prüfen** shows the latest schedule — generated or imported — with its independent check, the duties, staffing and monthly accounts, and offers publication, downloads and import. Nothing is saved, and nothing is published until you [publish it explicitly](publication.md); the schedule is kept only until the API restarts. The procedure below is checked with controlled browser flows and fictional data and with a live January run on the prepared test database; see [current limitations](../validation/index.md#review-import-and-export).

Return to the [documentation overview](index.md).

## Read the status and act on it

After a generation that found a schedule, _Letzte Generierung_ on **Erstellen** links to **Dienstplan prüfen** with the job's month and stations. A generation without a schedule (infeasible, no result in time, failed) leaves the previous schedule under review.

The page always reviews one schedule, from top to bottom: its summary with the actions, the wishes, the duty grid and the monthly accounts. Wishes and monthly accounts start collapsed; select their title to open them. The summary card is headed with the month and stations and names whether the schedule was generated or imported and when, and its number of duties. One status line says whether it may be used:

- **Regeln eingehalten · Kann veröffentlicht werden**: the independent check accepted it. With gaps, the line adds _Lücken werden nicht veröffentlicht_.
- **Regelverstöße**: the schedule breaks a rule and is not usable. A box below lists every finding with its rule, message, employee, date and station.
- **Unvollständig geprüft**: a check promised for the month lacked input; the box lists the missing inputs with their dates.

Only an accepted schedule is usable; any other one is a diagnosis. The check, not the solver, decides.

When required slots stay unfilled, an amber box **Lücken** follows: _n unbesetzte Pflichtstellen_, one line per station, date, shift and qualification with how many staff are missing and how many are required. The same slots are marked in the grid's **Besetzung** rows. No eligible employee was free for them, so request guest staff for these shifts. Gaps are never published as duties; the check accepts a schedule only if every shortfall is listed exactly.

When the month has wishes, the collapsed card **Wünsche** below the summary is titled with what the schedule made of the month's wishes (_erfüllt_, _nicht erfüllt_, _nicht erfüllbar_); opened, it shows a table of every wish by date with employee, wish and outcome. _Nicht erfüllbar_ means that the inputs of its own day rule it out: an availability entry, a missing membership or the shift's own work rules for a wished day or shift, a trusted duty touching a wished free day. It does not count against the schedule. A wish that only the rules across days prevent, such as the rest after a trusted night, is _nicht erfüllt_. Wishes never bind.

Next to the status sit the actions: **In TimeOffice veröffentlichen** (only for an accepted schedule; see [publication](publication.md)), **Herunterladen**, **Importieren** and **Veröffentlichte Dienste entfernen**. Each opens a small panel. **Herunterladen** lists the files; **Importieren** replaces the review only after **Dateien importieren** and a successful validation; publishing and removal change TimeOffice only after their confirmation button.

If the header selection is another month or other stations, the page says so instead of showing the schedule as the selected one; **Zu diesem Umfang wechseln** selects the schedule's own scope. Without a schedule, the card offers import and removal only.

The collapsed section **Technische Details** is for diagnosing a run, not needed to use the schedule: the solver status, run time and limit, search threads, random seed, one line per objective stage in solving order (**Stufe 1: Lücken** to **Stufe 6: Überzählige Zwischendienste**) with its value and either _optimal_ or its proven bound (_Schranke_, a weak bound is not a broken rule), the check's scores (gaps, health events from six-day runs, backward shift changes, isolated workdays and back-to-back worked weekends, station transfers, the wish cost, total account deviation, surplus intermediate duties), obligations beyond the month that cannot be assessed here (the next month's start, annual free Sundays) and any solver diagnostics with their code and English message.

## Inspect employee and unit schedules

The card _Dienstplan_ lists every participating employee by date — ID, name and every home unit of the month, each on one line; a long name is cut and shown in full on pointing — also employees without duties. A duty shows only its shift code in the shift colour (Früh, Zwischen, Spät, Nacht): the employee column already names where they belong. Pointing at a duty shows station, shift and times, credited qualification and origin, and screen readers read the same text.

Only a duty worked outside its origin — the employee's home station or jumper pool _on that date_, as the backend dates it — is highlighted as a transfer by a dashed border. With more than one station selected, a transfer also names the station where it is worked by a short code (a short name as is, a longer one by its initials, for example _ESN_; full names if two initials would be the same); the legend lists the codes. A duty whose employee has no dated home is tagged **?** (_Herkunft unbekannt_); the check reports it as an eligibility finding. The comparison never uses the row's home units, so a home change within the month is shown per date. Native TimeOffice absences show their absence code (for example `U`, `SC`), project availability its short code (`–` not available, `U` vacation, `FB` training, `Fr` free, `nur` only certain shifts) with the reason on pointing; weekends and public holidays are shaded; a red frame marks an employee and date with a finding. Below, **Besetzung** gives for each station and shift the filled against the required slots per date; each qualification counts up to its own demand, because another qualification never fills it and a surplus never covers another's gap. Where nothing is required, it shows the assigned staff against `0`. A gap cell is tinted red and shows the missing staff under the count (for example `1/2` over `−1`); pointing at a number names the missing qualification and lists the assigned against the required staff per qualification, surplus included.

Search by name or ID, or open **Vollbild** (leave with the button or Esc). The legend under the table explains exactly the marks this schedule shows: its shift types, transfers and station codes, absence and availability codes, rule violations and gaps only when they occur. On narrow screens the grid scrolls horizontally; the employee column stays in place.

_Monatskonten_, collapsed and titled with the number of employees, lists every employee's **Soll**, **Gutschriften**, **Geplant** and **Saldo** (Geplant + Gutschriften − Soll) in hours and minutes, as the backend computed them; a balance outside the allowed band is marked when the check reports it.

## Import and validate a portable bundle

1. Select **Importieren** and choose an `input.json` and its `result.json`.
2. Select **Dateien importieren**.

The backend validates the pair before replacing the schedule under review: both files must be format version 2 without unknown fields, `result.json` must name the SHA-256 digest of exactly this `input.json` and its month, contain a found schedule whose assignments and gaps reference the input's employees, stations and shifts within the month, have been solved with the current rule settings, and carry a schedule check equal to an independent re-check. A rejected pair shows why in the panel (invalid files, files that do not belong together, no schedule, other rule settings, unknown duties, a differing check) and _Der bisherige Dienstplan bleibt zur Prüfung_: the current review and its downloads stay unchanged. A valid pair closes the panel and replaces the review. An import never publishes and never stores a copy.

## Download JSON and CSV files

**Herunterladen** lists the five files of the schedule under review: `input.json`, `result.json`, `schedule.csv`, `employees.csv` and `gaps.csv`. Their fields are described under [examples and reproduction](../validation/examples.md#bundle-files). The files need no saved schedule library and can be read, re-solved and checked without TimeOffice. For a schedule that is not accepted, the list states that the files are a diagnosis, not a usable schedule.
