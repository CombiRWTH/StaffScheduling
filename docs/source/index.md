# Staff Scheduling

A hospital planning application combining a Next.js webapp, a FastAPI API and an OR-Tools CP-SAT solver. A TimeOffice adapter reads planning inputs and writes assignments to an external SQL Server. The current checkout starts both services; connected planning and independently accepted example schedules are still being completed.

## Find what you need

| You are here to…                       | Start here                                            | What you will find                                                |
| -------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------- |
| Try the application                    | [Quickstart](getting-started/quickstart.md)           | Docker, just, the password file and one startup command           |
| Set up a machine                       | [Installation](getting-started/installation.md)       | Prerequisites, configuration, network access and troubleshooting  |
| Use the application                    | [Use guide](user-guide/index.md)                      | Staff-admin operations, with unfinished procedures clearly marked |
| Understand the system                  | [Architecture](architecture/index.md)                 | Code map, data flow, domain and integration contracts             |
| Change the code                        | [Development checks](development/checks.md)           | Tooling, quality gates and where tests/docs belong                |
| Assess what has been proved            | [Evidence and limitations](validation/index.md)       | Executed checks, current failures and unverified behavior         |
| Inspect or reproduce example results   | [Examples](validation/examples.md)                    | An outline until accepted files and reproduction checks exist     |
| Examine the reasoning behind the model | [Reasoning and requirements](validation/reasoning.md) | An outline for sourced rules, choices and evaluation              |

## What is ready to try

Docker startup and the webapp home/API liveness pages have been checked. Start with the quickstart to inspect this foundation. A healthy process does not establish database access or a supported complete planning workflow. Visible controls and source-defined routes are not scheduling acceptance evidence.

This site separates setup, staff-admin tasks, technical understanding, contribution procedures and validation. Each page has one purpose; [documentation maintenance](development/documentation.md) describes how verified changes fill the outlines and keep these perspectives consistent.
