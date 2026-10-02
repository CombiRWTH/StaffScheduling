# Generation and job states

**Dienstplan → Erstellen** generates a schedule for the whole planning month and the selected stations, and checks every schedule found independently against the planning rules. Nothing is written to TimeOffice. The procedure below has been checked with controlled browser flows and fictional data and with live runs on the prepared test database; see [current limitations](../validation/index.md#solver-and-schedule-check).

Return to the [documentation overview](index.md).

## Inspect inputs before generation

A run uses, for the selection:

- the employees of the selected stations and of the jumper pools their members call home, with dated memberships and qualifications ([Mitarbeiter](selection.md));
- monthly accounts with their dated absence credits;
- native TimeOffice absences and project availability entries ([Verfügbarkeit](configuration.md));
- the saved **Mindestbesetzung** of every selected station for that month;
- the four reference shifts with their TimeOffice target times, breaks and paid minutes;
- trusted duties of the days before and after the month, from TimeOffice's context plans.

It does not use wishes or existing worked shifts in any other TimeOffice roster (including earlier output in the target plan). Jumper pool employees can only be planned at a station where they have a membership. A station whose staffing was never saved is refused instead of being planned with zero demand.

Check the employee page for completeness first: generation reads the same facts and refuses incomplete ones.

## Start a full-month run

1. Choose the month and one or more stations in the header.
2. Open **Dienstplan erstellen**. The card _Neue Generierung_ repeats the period and stations and lists which inputs are and are not used; a run always covers the whole month.
3. Enter the **maximale Laufzeit** in seconds (30–3600, default 30). This is the solver's search limit; reading the data and preparing the model come on top.
4. Select **Starten**.

The backend first reads and checks all inputs. If something is missing, a message appears under the button and no job starts: an incomplete or unsaved input asks to save every station's staffing and to check the employee data; an invalid selection or time limit names what to choose; an unreachable TimeOffice or a failed TimeOffice query (schema, permissions) says so. Otherwise the job appears under _Letzte Generierung_ as **Läuft**.

## Follow status and handle failures

The page refreshes itself every two seconds while the job runs. You can leave it and come back through **Erstellen**: the latest job is shown again.

The card _Letzte Generierung_ shows the job's month and stations and three separate outcomes:

| Outcome       | Values                                                                                                                                                                                                                                |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ablauf        | **Läuft**, **Abgeschlossen** (the solver finished, whatever it found) or **Fehlgeschlagen** (an unexpected error; details are in the API log)                                                                                         |
| Solver-Status | **Optimale Lösung**, **Lösung gefunden** (optimum not proven), **Keine Lösung möglich** (proven infeasible), **Keine Lösung innerhalb der Laufzeit**, or **Modell ungültig**                                                          |
| Prüfung       | **Regeln eingehalten** (every checked rule kept), **Regelverstöße** (the schedule breaks a rule and is not usable), **Unvollständig geprüft** (a rule lacked input, for example the days before the month) or **Kein Plan zu prüfen** |

Below them are the counts of generated duties and solver diagnostics, and the violated and not-assessed rules by name with their counts. The [review](review.md) shows the optimality gap and the solver details. _Nicht bewertet … (über den Monat hinaus)_ lists obligations that a month cannot decide, such as annual free Sundays; they do not prevent acceptance. _(fehlende Eingaben)_ means a check promised for the month had no input and the schedule is not accepted. Nothing is published automatically.

With a found schedule, **Dienstplan prüfen** opens its [review](review.md): every duty, finding, account and the downloads.

If the job runs well beyond its time limit, the page stops refreshing and asks you to reload; if it stays on **Läuft**, check the API log. For **Keine Lösung möglich**, read the diagnostics in the job (`GET /generation`): a message such as "needs 2 professional … but only 0 can work it" names the station, date and shift whose demand no employee can cover after availability and the context duties are taken into account. Then check that day's staffing demand, availability, memberships and context duties. For **Fehlgeschlagen**, check the API log; the page deliberately shows no internal error text.

## Restart and concurrency behavior

The backend runs one generation at a time. Starting another while one runs is refused with _Es läuft bereits eine Generierung_; start again after it has finished. On this page the button is disabled while a job runs.

Jobs are kept in the API process only. After an API restart (also a source reload during development) the page shows _Kein Ergebnis verfügbar_: results of earlier jobs are lost and a job that was running is not resumed. The application must run as a single API process; a second process would have its own lock and jobs.
