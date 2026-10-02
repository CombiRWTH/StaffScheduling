# Use the application

Start the services with `just run` as described in the [quickstart](../getting-started/quickstart.md), then open <http://localhost:3000>. Every step below passes controlled browser flows on fictional data; [current limitations](../validation/index.md) record which steps were also run against the prepared test database and what is not supported.

## What you can use this guide for

For staff administrators using the application: choose the month and units, inspect employees, configure availability and staffing, generate schedules, review or exchange files, then publish or clear assignments. Each procedure explains what to do, what result to expect and how to recover from a failure. All of them are checked with controlled browser flows on fictional data; the [limitations](../validation/index.md) page records which were also run against the prepared test database.

## Planning concepts

The backend models a calendar month, planning units, dated staffing demand, employees and valid unit memberships. Availability entries are binding; wishes are preferences that generation considers fairly but never guarantees. Work accounts are stored in minutes and shown in hours and minutes (for example _160:00 h_). The [domain reference](../architecture/domain.md) describes the source-defined contract.

## Planning steps

The overview (**Übersicht**) welcomes you with a short introduction and lists the planning steps in their usual order: **Schritt 1 Mitarbeiter**, **Schritt 2 Verfügbarkeit**, **Schritt 3 Mindestbesetzung**, **Schritt 4 Dienstplan erstellen** and **Schritt 5 Dienstplan prüfen**. Each card opens its page with the selected month and stations.

1. Choose month and stations in the planning selection beside the title of any page.
2. Open **Schritt 1** on the overview. The pages of steps 1 to 3 end with a link such as **Weiter mit Schritt 2: Verfügbarkeit**, which keeps the selection. Unsaved availability or demand edits are not kept when you leave a page; save them first.
3. On **Dienstplan erstellen**, start the run. When a schedule was found, **Dienstplan prüfen** opens the review.
4. On **Dienstplan prüfen**, review the schedule, then download it or publish it to TimeOffice. Publication and clear each need their own confirmation; nothing is published automatically.

The steps are a suggestion, not a lock: the sidebar and the back arrow before every page title reach any page at any time, and each page works with the selection in the URL. Recurring availability, templates, a file library, schedule comparison and optimization settings are not part of the application.

## Find an operation

Follow the planning flow from top to bottom:

1. [Select a month and inspect employees](selection.md).
2. [Configure monthly inputs](configuration.md).
3. [Generate and follow a job](generation.md).
4. [Review, import and export](review.md).
5. [Publish or clear a scope](publication.md).

The [API reference](../architecture/api.md) describes current route definitions. The [example guide](../validation/examples.md) describes the bundle files and the commands that solve and validate them without TimeOffice.
