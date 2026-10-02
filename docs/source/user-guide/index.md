# Use the application

Start through the [quickstart](../getting-started/quickstart.md), then open <http://localhost:3000>. Service startup has been checked; the complete staff-admin planning workflow has not. Consult [current limitations](../validation/index.md) before treating visible controls or generated files as supported operations.

## What you can use this guide for

For staff administrators using the application: choose the month and units, inspect employees, configure availability and staffing, generate schedules, review or exchange files, then publish or clear assignments. Each procedure explains what to do, what result to expect and how to recover from a failure. All of them are checked with controlled browser flows on fictional data; the [limitations](../validation/index.md) page records which were also run against the prepared test database.

## Planning concepts

The backend models a calendar month, planning units, dated staffing demand, employees and valid unit memberships. Availability entries are binding; wishes are preferences that generation does not consider yet. Work accounts are stored in minutes and shown in hours and minutes (for example _160:00 h_). The [domain reference](../architecture/domain.md) describes the source-defined contract.

The overview (**Übersicht**) welcomes you with a short introduction and links every planning area: employee inspection, monthly configuration (Verfügbarkeit, Mindestbesetzung), generation (Erstellen) and review (Prüfen). The sidebar links the overview and each area.

## Find an operation

Follow the planning flow from top to bottom:

1. [Select a month and inspect employees](selection.md).
2. [Configure monthly inputs](configuration.md).
3. [Generate and follow a job](generation.md).
4. [Review, import and export](review.md).
5. [Publish or clear a scope](publication.md).

The [API reference](../architecture/api.md) describes current route definitions. The [example guide](../validation/examples.md) describes the bundle files and the commands that solve and validate them without TimeOffice.
