# Staff Scheduling

A hospital planning application combining a Next.js webapp, a FastAPI API and an OR-Tools CP-SAT solver. A TimeOffice adapter reads planning inputs and writes assignments to an external SQL Server.

## Find what you need

| You are here to…                       | Start here                                            | What you will find                                                           |
| -------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------- |
| Try the application                    | [Quickstart](getting-started/quickstart.md)           | Docker, just, the password file and one startup command                      |
| Set up a machine                       | [Installation](getting-started/installation.md)       | Prerequisites, configuration, network access and troubleshooting             |
| Use the application                    | [Use guide](user-guide/index.md)                      | Staff-admin operations from selection to publication, and the planning rules |
| Understand the system                  | [Architecture](architecture/index.md)                 | Code map, data flow, domain and integration contracts                        |
| Change the code                        | [Development checks](development/checks.md)           | Tooling, quality gates and where tests/docs belong                           |
| Assess what has been proved            | [Evidence and limitations](validation/index.md)       | Executed checks, current failures and unverified behavior                    |
| Inspect or reproduce example results   | [Examples](validation/examples.md)                    | Committed example schedules and how to check them without TimeOffice         |
| Examine the reasoning behind the model | [Reasoning and requirements](validation/reasoning.md) | Sourced rules, modeling choices and evaluation                               |

## What is ready to try

Start with the [quickstart](getting-started/quickstart.md), then follow the [user guide](user-guide/index.md) from selection to publication. Planning pages need access to a prepared TimeOffice database; the [example schedules](validation/examples.md) can be checked without it. [Evidence and limitations](validation/index.md) record what was verified.

This site separates setup, staff-admin tasks, technical understanding, contribution procedures and validation. Each page has one purpose; [documentation maintenance](development/documentation.md) describes how changes keep these perspectives consistent.
