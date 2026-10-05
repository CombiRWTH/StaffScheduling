# Generation and job states

**Dienstplan → Erstellen** generates a schedule for the whole planning month and the selected stations. Every schedule found is checked independently against the [planning rules](rules.md). Nothing is written to TimeOffice. See [current limitations](../validation/index.md#solver-and-schedule-check) for what has been checked.

Return to the [documentation overview](index.md).

## Inspect inputs before generation

A run uses, for the selection:

- the employees of the selected stations and of the jumper pools their members call home, with dated memberships and qualifications ([Mitarbeiter](selection.md));
- monthly accounts with their dated absence credits;
- native TimeOffice absences, project availability entries and wishes ([Verfügbarkeit](configuration.md)), including those of jumper pool employees;
- the saved **Mindestbesetzung** of every selected station for that month;
- the four reference shifts with their TimeOffice target times, breaks and paid minutes;
- trusted duties of the days before and after the month, from TimeOffice's context plans.

It does not use native TimeOffice wish rows. It also ignores existing worked shifts in any other TimeOffice roster, including earlier output in the target plan. Jumper pool employees can only be planned at a station where they have a membership. A station whose staffing was never saved is refused; it is not planned with zero demand.

Check the employee page for completeness first. Generation reads the same facts and refuses incomplete ones.

## Start a full-month run

1. Choose the month and one or more stations in the header.
2. Open **Dienstplan erstellen**. The start card is headed with the month and stations it will plan, always the whole month. It lists the inputs it uses (**Berücksichtigt**) and does not use (**Nicht berücksichtigt**).
3. Next to **Starten**, enter the **Maximale Laufzeit** in seconds (30–3600, default 30; the field shows the unit _s_). This is the solver's total search limit, shared by its stages (gaps, health, station transfers, wishes, monthly accounts, intermediate duties). Reading the data and preparing the model come on top. The seven-station examples use 1,800 seconds per month and still do not prove the minimum gap count ([results](../validation/examples.md#results)). Short limits can leave additional unfilled slots.
4. Select **Starten**.

The backend first reads and checks all inputs. If something is missing, a message appears under the start row and no job starts:

- an incomplete or unsaved input asks you to save every station's staffing and to check the employee data;
- an invalid selection or time limit names what to choose;
- an unreachable TimeOffice or a failed TimeOffice query (schema, permissions) says so.

Otherwise the job appears under _Letzte Generierung_ as running.

## Follow status and handle failures

While the job runs, the page refreshes itself every two seconds. You can leave it and come back through **Erstellen**; the latest job is shown again.

The card _Letzte Generierung_ names the job's month and stations. One headline states the outcome and what to do next:

| Headline                                        | Meaning and next step                                                                                 |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Dienstplan wird berechnet …                     | The job runs, up to its time limit.                                                                   |
| Dienstplan erstellt, Regeln eingehalten         | Accepted: open **Dienstplan prüfen** to review and publish it; it is not published automatically.     |
| Dienstplan erstellt, aber unvollständig geprüft | A check promised for the month lacked input (for example the days before the month); not publishable. |
| Dienstplan erstellt, aber mit Regelverstößen    | The schedule breaks a rule and is not usable.                                                         |
| Kein Dienstplan möglich                         | The inputs contradict each other (proven infeasible) outside staffing; the hints name where.          |
| Keine Lösung innerhalb der Laufzeit             | Start again with a longer time limit.                                                                 |
| Generierung fehlgeschlagen / Modell ungültig    | An unexpected error; details are in the API log. The page shows no internal error text.               |

A row of facts follows:

- **Ablauf**: Läuft, Abgeschlossen or Fehlgeschlagen.
- **Zeit**: start and end of the job.
- **Solver**: Wird berechnet …, Optimale Lösung, Lösung gefunden, Keine Lösung möglich, Keine Lösung innerhalb der Laufzeit, Modell ungültig or Kein Ergebnis.
- **Prüfung**: Wartet auf Plan, Regeln eingehalten, Regelverstöße, Unvollständig geprüft or Kein Plan zu prüfen.
- **Dienste**: the number of duties.
- **Lücken**: required slots no employee could fill. A schedule with gaps can still be accepted.

When a run is not usable, a box says why:

- **Hinweise** sums up the solver's warnings and errors in German, one line per kind with its count. For example, _Mindestbesetzung nicht erreichbar: Für 2 Schichten gibt es zu wenige einsetzbare Mitarbeiter; sie bleiben als Lücken offen_ explains gaps; it does not prevent a schedule.
- **Verstöße** names the violated rules with their counts.
- **Fehlende Eingaben** names the rules that lacked input, with their dates.

For **Kein Dienstplan möglich**, check the named demand, availability, memberships and context duties.

The collapsed **Technische Details** are for developers. They show:

- the job ID, the solver status with its explanation and the search time used;
- how many objective stages proved their optimum (**Zielstufen**);
- every solver diagnostic with its severity, code and the backend's English message, such as "Station 101 needs 2 professional on 2026-08-05 (shift 1113), but only 0 can work it." (station, date and shift by ID);
- obligations a month cannot decide, such as annual free Sundays (_Über den Monat hinaus, hier nicht bewertet_). They do not prevent acceptance.

`GET /generation` returns the same data. A failed job's internal error is written only to the API log.

With a found schedule, **Dienstplan prüfen** opens its [review](review.md): every duty, finding, account and the downloads. If the job runs well beyond its time limit, the page stops refreshing and asks you to reload. If it stays running, check the API log.

## Restart and concurrency behavior

The backend runs one generation at a time. While one runs, the start button is disabled. Another start request is refused with _Es läuft bereits eine Generierung_; start again after the job has finished.

Jobs are kept in the API process only. An API restart, including a source reload during development, loses them. The page then shows _Kein Ergebnis verfügbar_, and a job that was running is not resumed. The application must run as a single API process, since a second process would have its own lock and jobs.
