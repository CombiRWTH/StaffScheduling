# Generation and job states

**Dienstplan → Erstellen** generates a schedule for the whole planning month and the selected stations, and checks every schedule found independently against the planning rules. Nothing is written to TimeOffice. The procedure below has been checked with controlled browser flows and fictional data and with live runs on the prepared test database; see [current limitations](../validation/index.md#solver-and-schedule-check).

Return to the [documentation overview](index.md).

## Inspect inputs before generation

A run uses, for the selection:

- the employees of the selected stations and of the jumper pools their members call home, with dated memberships and qualifications ([Mitarbeiter](selection.md));
- monthly accounts with their dated absence credits;
- native TimeOffice absences, project availability entries and wishes ([Verfügbarkeit](configuration.md)), including those of jumper pool employees;
- the saved **Mindestbesetzung** of every selected station for that month;
- the four reference shifts with their TimeOffice target times, breaks and paid minutes;
- trusted duties of the days before and after the month, from TimeOffice's context plans.

It does not use native TimeOffice wish rows or existing worked shifts in any other TimeOffice roster (including earlier output in the target plan). Jumper pool employees can only be planned at a station where they have a membership. A station whose staffing was never saved is refused instead of being planned with zero demand.

Check the employee page for completeness first: generation reads the same facts and refuses incomplete ones.

## Start a full-month run

1. Choose the month and one or more stations in the header.
2. Open **Dienstplan erstellen**. The start card is headed with the month and stations it will plan (always the whole month) and, in one line, which inputs are and are not used.
3. Next to **Starten**, enter the **Maximale Laufzeit** in seconds (the field shows the unit _s_) (30–3600, default 30). This is the solver's total search limit, shared by its stages (gaps, health, wishes, monthly accounts, intermediate duties); reading the data and preparing the model come on top. A real month of both example stations needs about 300 seconds for good health scores.
4. Select **Starten**.

The backend first reads and checks all inputs. If something is missing, a message appears under the start row and no job starts: an incomplete or unsaved input asks to save every station's staffing and to check the employee data; an invalid selection or time limit names what to choose; an unreachable TimeOffice or a failed TimeOffice query (schema, permissions) says so. Otherwise the job appears under _Letzte Generierung_ as running.

## Follow status and handle failures

The page refreshes itself every two seconds while the job runs. You can leave it and come back through **Erstellen**: the latest job is shown again.

The card _Letzte Generierung_ names the job's month and stations and states its outcome in one line with what to do next:

| Headline                                        | Meaning and next step                                                                                 |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Dienstplan wird berechnet …                     | The job runs, up to its time limit.                                                                   |
| Dienstplan erstellt, Regeln eingehalten         | Accepted: open **Dienstplan prüfen** to review and publish it; nothing is published automatically.    |
| Dienstplan erstellt, aber unvollständig geprüft | A check promised for the month lacked input (for example the days before the month); not publishable. |
| Dienstplan erstellt, aber mit Regelverstößen    | The schedule breaks a rule and is not usable.                                                         |
| Kein Dienstplan möglich                         | The inputs contradict each other (proven infeasible) outside staffing; the hints name where.          |
| Keine Lösung innerhalb der Laufzeit             | Start again with a longer time limit.                                                                 |
| Generierung fehlgeschlagen / Modell ungültig    | An unexpected error; details are in the API log. The page deliberately shows no internal error text.  |

A row of facts follows: **Ablauf** (Läuft, Abgeschlossen, Fehlgeschlagen), **Zeit**, **Solver** (Wird berechnet …, Optimale Lösung, Lösung gefunden, Keine Lösung möglich, Keine Lösung innerhalb der Laufzeit, Modell ungültig, Kein Ergebnis), **Prüfung** (Wartet auf Plan, Regeln eingehalten, Regelverstöße, Unvollständig geprüft, Kein Plan zu prüfen) the number of **Dienste** and of **Lücken** (required slots no employee could fill; a schedule with gaps can still be accepted).

When a run is not usable, a box says why: **Hinweise** sums up the solver's warnings and errors in German, one line per kind with its count (for example _Mindestbesetzung nicht erreichbar: Für 2 Schichten gibt es zu wenige einsetzbare Mitarbeiter; sie bleiben als Lücken offen_, which explains gaps rather than preventing a schedule), **Verstöße** names the violated rules with their counts and **Fehlende Eingaben** the rules that lacked input, with their dates. For **Kein Dienstplan möglich**, check the named demand, availability, memberships and context duties.

The collapsed **Technische Details** are for developers: the job ID, the solver status with its explanation, the search time used, how many objective stages proved their optimum (**Zielstufen**), every solver diagnostic with its severity, code and the backend's English message (such as "Station 101 needs 2 professional on 2026-08-05 (shift 1113), but only 0 can work it.", naming station, date and shift by ID), and obligations a month cannot decide (_über den Monat hinaus_, such as annual free Sundays), which do not prevent acceptance. The same data is available from `GET /generation`. A failed job's internal error is written only to the API log.

With a found schedule, **Dienstplan prüfen** opens its [review](review.md): every duty, finding, account and the downloads. If the job runs well beyond its time limit, the page stops refreshing and asks you to reload; if it stays running, check the API log.

## Restart and concurrency behavior

The backend runs one generation at a time. Starting another while one runs is refused with _Es läuft bereits eine Generierung_; start again after it has finished. On this page the button is disabled while a job runs.

Jobs are kept in the API process only. After an API restart (also a source reload during development) the page shows _Kein Ergebnis verfügbar_: results of earlier jobs are lost and a job that was running is not resumed. The application must run as a single API process; a second process would have its own lock and jobs.
