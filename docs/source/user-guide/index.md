# Use the application

This guide is for staff administrators. It walks through one planning month: choose the month and stations, inspect employees, configure availability and staffing, generate a schedule, review or exchange its files, then publish or clear assignments. Each page explains what to do, what result to expect and how to recover from a failure. [Current limitations](../validation/index.md) record how each step was checked and what is not supported.

Start the services with `just run` as described in the [quickstart](../getting-started/quickstart.md), then open <http://localhost:3000>.

## Planning concepts

The backend models a calendar month, planning units, dated staffing demand, employees and valid unit memberships. Availability entries are binding. Wishes are preferences that generation considers fairly but never guarantees. Work accounts are stored in minutes and shown in hours and minutes (for example _160:00 h_). The [domain reference](../architecture/domain.md) describes the source-defined contract. The [planning rules](rules.md) explain which rules a schedule keeps and how generation chooses between schedules.

## Planning steps

The overview (**Übersicht**) opens with a short welcome. It lists the planning pages as cards in their usual order. Each card opens its page with the selected month and stations.

1. Choose month and stations in the planning selection beside the title of any page; see [selection and employees](selection.md).
2. Open **Mitarbeiter** to inspect employees, their memberships and accounts.
3. Edit **Verfügbarkeit** and **Mindestbesetzung**; see [monthly configuration](configuration.md). Unsaved edits are lost when you leave a page, so save them first.
4. On **Dienstplan erstellen**, start the run; see [generation](generation.md). When a schedule was found, **Dienstplan prüfen** opens the review.
5. On **Dienstplan prüfen**, [review the schedule](review.md), download or import files, then [publish or clear](publication.md) it in TimeOffice.

!!! warning

    Publication and clear each need their own confirmation; nothing is published automatically.

The steps are a suggestion, not a lock. The sidebar reaches any page at any time, and the back arrow before a page title returns to the overview. Every page works with the selection in the URL. Recurring availability, templates, a file library, schedule comparison and optimization settings are not part of the application.

The [API reference](../architecture/api.md) describes current route definitions. The [example guide](../validation/examples.md) describes the bundle files and the commands that solve and validate them without TimeOffice.
