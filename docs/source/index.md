# Staff Scheduling

Staff Scheduling supports hospital staff planning with a Next.js webapp, a FastAPI API and Google OR-Tools CP-SAT. It was developed at RWTH Aachen University with St. Marien-Hospital Düren and Pradtke GmbH. TimeOffice provides the employee, shift and planning data.

Start with the [quickstart](quickstart.md) to launch both services using Docker. The [installation guide](installation.md) covers prerequisites, configuration, network access and optional developer tools.

| You want to…                                   | Read                                                                                                                         |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Start the application                          | [Quickstart](quickstart.md)                                                                                                  |
| Set up another machine or troubleshoot startup | [Installation](installation.md)                                                                                              |
| Understand the planning screens                | [Using the app](usage.md)                                                                                                    |
| Check what works and what remains unfinished   | [Current limitations](limitations.md)                                                                                        |
| Find the relevant code                         | [Codebase overview](development/overview.md)                                                                                 |
| Run checks or change dependencies              | [Code quality](development/quality.md)                                                                                       |
| Understand backend contracts                   | [API](reference/api.md), [domain](reference/domain.md), [solver](reference/solver.md), [TimeOffice](reference/timeoffice.md) |

Both services can start before a database connection is established. Planning operations need the configured TimeOffice database. The application is undergoing integration work; [current limitations](limitations.md) distinguish service startup from verified scheduling and publication.
