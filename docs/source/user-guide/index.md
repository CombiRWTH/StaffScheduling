# Use the application

Start through the [quickstart](../getting-started/quickstart.md), then open <http://localhost:3000>. Service startup has been checked; the complete staff-admin planning workflow has not. Consult [current limitations](../validation/index.md) before treating visible controls or generated files as supported operations.

## What you can use this guide for

For staff administrators using the application: choose the month and units, inspect employees, configure availability and staffing, generate schedules, review or exchange files, then publish or clear assignments. Each procedure will explain what to do, what result to expect and how to recover from a failure. Selection, configuration and generation are checked with controlled browser flows; review, file exchange and publication remain outlines until their acceptance checks pass.

## Planning concepts

The backend models a calendar month, planning units, dated staffing demand, employees and valid unit memberships. Availability entries are binding; wishes are preferences that generation does not consider yet. Work accounts use minutes. The [domain reference](../architecture/domain.md) describes the source-defined contract.

The home page, employee inspection and monthly configuration (Verfügbarkeit, Mindestbesetzung) are implemented. The sidebar lists every other planning area greyed out as not yet supported.

## Find an operation

These pages are outlines to fill as each operation is verified. Their headings do not establish feature support.

1. [Select a month and inspect employees](selection.md).
2. [Configure monthly inputs](configuration.md).
3. [Generate and follow a job](generation.md).
4. [Review, import and export](review.md).
5. [Publish or clear a scope](publication.md).

The [API reference](../architecture/api.md) describes current route definitions. The [example guide](../validation/examples.md) reserves the reproduction instructions for accepted files once they exist.
