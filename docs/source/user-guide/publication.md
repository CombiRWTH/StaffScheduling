# Publication and clear

**Dienstplan → Prüfen** can write the schedule under review into the stations' TimeOffice planning targets, and remove published duties again. Nothing else publishes: generation and import only replace the schedule under review. The procedure below is checked with controlled browser flows and fictional data and with live runs on the prepared test database; see [current limitations](../validation/index.md#publication-and-clear).

Return to the [documentation overview](index.md).

## Confirm accepted result and target scope

The card _Veröffentlichen_ on **Prüfen** names the selected stations and month, the scope it writes to. Publishing is offered only when

- the schedule under review belongs to exactly this selection (otherwise **Zu diesem Umfang wechseln** selects the schedule's own scope), and
- its independent check is **Regeln eingehalten** (accepted). For a rejected or incompletely checked schedule the card says that only an accepted schedule can be published.

Each selected station needs one TimeOffice target plan for the month, the same plan the [selection](selection.md) offers.

The review itself does not show whether its schedule is published: only the card's message after a confirmed publication or clear reports it, and that message is gone after a reload.

## Publish assignments

1. Select **In TimeOffice veröffentlichen**. The card asks for confirmation and names the stations, the month and the number of duties. **Abbrechen** changes nothing.
2. Select **Veröffentlichen bestätigen**.

The backend replaces the duties previously published in the stations' target plans with the reviewed duties. A jumper pool employee's duty goes into the plan of the station where it is worked. Published duties carry the note `StaffScheduling` in TimeOffice; absences, TimeOffice wishes, duties entered in TimeOffice and every other plan stay unchanged. Success reads _Veröffentlicht: N Dienste geschrieben und gelesen, M bisherige ersetzt_; it appears only after TimeOffice committed the change and the written duties were read back identical to the schedule.

Publishing again replaces the earlier publication. A schedule without duties is not offered for publication. A schedule generated later, even for the same scope, must be reviewed before it can be published: a request for a schedule that is no longer the one under review is refused.

## Clear an explicit scope

Clearing is maintenance and does not need a schedule under review.

1. Select the month and stations in the header.
2. Under _Wartung_, select **Veröffentlichte Dienste entfernen**. The card names the exact stations and month; **Abbrechen** changes nothing.
3. Select **Entfernen bestätigen**.

All published duties of those station months are removed; absences, wishes, duties entered in TimeOffice and other plans stay. Success reads _Entfernt: N veröffentlichte Dienste_. There is no empty publication: a schedule without duties is refused, so clearing is always this explicit action.

## Failures, rollback and verification

A refused or failed publication changes nothing in TimeOffice. Everything is checked before the old duties are deleted, in the same transaction that writes the new ones; any later failure rolls the whole change back.

| Message                                                                                                                            | Meaning and next step                                                                                                                                                                                                        |
| ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| _Der Dienstplan zur Prüfung hat sich geändert …_                                                                                   | Another generation or import replaced the schedule after the page loaded. Reload and review it.                                                                                                                              |
| _Nur ein angenommener Dienstplan kann veröffentlicht werden._                                                                      | The schedule is not accepted.                                                                                                                                                                                                |
| _TimeOffice enthält an einem Diensttag bereits eine Abwesenheit …_                                                                 | An employee has an absence or another duty on one of the dates: entered after the generation, entered in TimeOffice in the target plan, or in another plan. Generate again with the current data, or remove the other entry. |
| _TimeOffice wurde gleichzeitig geändert …_                                                                                         | Another writer changed the same rows at the same time and the change was rolled back. Try again.                                                                                                                             |
| _TimeOffice hat die Dienste anders gespeichert als geschrieben …_                                                                  | The rows read back differ from the schedule, for example because TimeOffice altered them on insert. Report it; the publication was rolled back.                                                                              |
| _TimeOffice-Daten für die Veröffentlichung sind unvollständig oder mehrdeutig …_                                                   | A station has several target plans, an employee lacks a station membership with the qualification of a duty, or shift data is missing. Fix the TimeOffice data.                                                              |
| _TimeOffice-Abfrage fehlgeschlagen … Nichts wurde geändert._ or _Backend oder TimeOffice nicht verfügbar … Nichts wurde geändert._ | The database refused or could not be reached and the transaction was rolled back.                                                                                                                                            |
| _Keine Antwort vom Backend: Ob TimeOffice geändert wurde, ist unbekannt …_ or _Verbindung beim Abschluss abgebrochen: …_           | No answer within two minutes, or the connection failed while TimeOffice was committing: the outcome is unknown. Reload the page and check the plan in TimeOffice before retrying.                                            |

To check a publication outside the application, compare the target plans' duties marked `StaffScheduling` in TimeOffice with `schedule.csv` of the reviewed schedule; the [TimeOffice adapter](../architecture/timeoffice.md#publication) describes how a duty is stored. Generating the month again does not read published duties, so a new run starts from the same inputs.
