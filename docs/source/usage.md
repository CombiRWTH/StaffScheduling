# Using the app

Start both services through the [quickstart](quickstart.md), then open <http://localhost:3000>. This page describes the planning concepts and the existing screens. The [limitations](limitations.md) page records unfinished operations; the full workflow is not yet verified end to end.

## Planning scope

A schedule covers a calendar month and one or more planning units. Stations carry staffing demand; shared pools are employee sources. An employee can work in a unit only when the input contains a valid membership interval. A pool label alone does not make every employee eligible.

The current UI still discovers cases through runtime files in `data/cases/`. The repository has no supplied case files, so its selector may be empty even while the API can list TimeOffice units. Canonical selection and employee inspection are still being connected.

## Inputs to inspect

| Area                            | Purpose                                                                  |
| ------------------------------- | ------------------------------------------------------------------------ |
| Employees                       | Identity, staffing level and relevant unit memberships                   |
| Availability and blocked shifts | Hard restrictions on when a person may work                              |
| Wishes                          | Preferences; distinct from hard availability restrictions                |
| Minimum staffing                | Required employee count for each unit, date, shift and staffing level    |
| Weights                         | Relative penalties for solver objectives; do not remove hard constraints |
| Existing assignments            | Planned work in selected units and external work that blocks employees   |
| Work accounts                   | Monthly target minutes and available recorded balances                   |

The UI contains employee, monthly/global configuration, templates, generation and schedule views. Existing template/global controls are compatibility features; their presence does not establish a supported canonical apply/overwrite workflow. Use the [API reference](reference/api.md) to distinguish implemented backend operations from frontend assumptions.

## Generate and review

The implemented backend accepts a full-month solve request, reads TimeOffice inputs, validates the domain dataset, runs CP-SAT and returns a transient job result. Only one solve can run in an API process at a time. Restarting or editing API source can discard jobs through development reload.

A job with status `succeeded` completed execution; inspect its result's solution status, diagnostics and audit separately. Infeasible or unknown results do not represent usable schedules. The current solver audit reuses solver components; independent acceptance is still pending.

Generated compatibility files and imported UI schedules have differing formats. Listing, import/export, comparison and publication are not yet a complete canonical workflow. Schedule publication is a separate database-writing operation, and its strengthened scope/acceptance checks remain unfinished. See [limitations](limitations.md) before using any result beyond inspection.
