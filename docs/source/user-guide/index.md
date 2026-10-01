# User guide

Start through the [quickstart](../getting-started/quickstart.md), then open <http://localhost:3000>. Service startup has been checked; the complete staff-admin planning workflow has not. Consult [current limitations](../validation/index.md) before treating visible controls or generated files as supported operations.

## Who this guide serves

For staff administrators who need to select a planning scope, inspect inputs, generate a roster, review it and explicitly publish it. The pages below reserve that task sequence; they will contain steps, expected outcomes and recovery paths after the workflows pass acceptance.

## Planning concepts

The backend models a calendar month, planning units, dated staffing demand, employees and valid unit memberships. Availability is a hard restriction; wishes are preferences. Work accounts use minutes. The [domain reference](../architecture/domain.md) describes the source-defined contract.

The imported UI still discovers cases in `data/cases/`. A fresh checkout has no case files. Its controls and compatibility formats are being reconciled with the backend; an empty selector is not proof that TimeOffice has no planning units.

## Workflow documentation

These pages are outlines to fill as each operation is verified. Their headings do not establish feature support.

1. [Select a month and inspect employees](selection.md).
2. [Configure monthly inputs](configuration.md).
3. [Generate and follow a job](generation.md).
4. [Review, import and export](review.md).
5. [Publish or clear a scope](publication.md).

The [API reference](../architecture/api.md) describes current route definitions. The [example guide](../validation/examples.md) reserves the reproduction instructions for accepted files once they exist.
