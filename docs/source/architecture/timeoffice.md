# TimeOffice adapter

This reference describes inspected source definitions. Connected database behavior and complete user workflows require separate acceptance evidence; see [current limitations](../validation/index.md).

`api/app/timeoffice/` owns the application's Microsoft SQL Server integration. `TimeOfficeService` coordinates reads, mapping, validation and transactional writes. The solver depends on the [domain model](domain.md), not the database schema.

## Modules

| Path under `api/app/timeoffice/` | Responsibility                                                                                 |
| -------------------------------- | ---------------------------------------------------------------------------------------------- |
| `database.py`                    | SQLAlchemy engine using `mssql+pyodbc`                                                         |
| `facts.py`                       | Reference identifiers, shift mappings and planning status assumptions                          |
| `reading/`                       | SQL readers for units, personnel, shifts, rosters, demand, wishes, accounts and Sunday history |
| `mapping/`                       | Source rows to canonical models/dataset                                                        |
| `remapping/`                     | Remaining frontend compatibility translations                                                  |
| `writing/`                       | Solution, wishes, availability, demand and objective-weight persistence; compatibility exports |
| `service.py`                     | Small entry points that coordinate these operations                                            |

## Connection and schema

Follow [database configuration](../getting-started/installation.md#database-configuration) for `.env` and the password file. Docker includes ODBC Driver 18. `database.py` constructs the SQLAlchemy URL from settings and currently uses `TrustServerCertificate=yes`. TLS policy/independent connectivity diagnostics still require foundation verification.

The adapter reads TimeOffice tables including `TPlanungseinheiten`, `TPlanungseinheitenPersonal`, `TPersonal`, `TPlan`, `TDienste`, `TPlanPersonalKommtGeht` and monthly/daily account tables. Actual SQL and join/filter rules are in the reader modules; this reference does not substitute a copied schema diagram for the database's current schema.

Minimum staffing and objective weights use `dbo.StaffSchedulingMinimalStaffing` and `dbo.StaffSchedulingObjectiveWeights`. The current reader/writer implementations can create these tables if missing, so apparently read-oriented configuration operations may need DDL permissions and may change the database. Coordinate table provisioning and permissions before using connected planning operations.

## Read and write boundaries

`fetch_dataset` normalizes selected unit IDs, reads source data, maps it and validates the aggregate. TimeOffice reductions and fixed reference mappings remain adapter behavior and must be checked against the chosen dataset.

Writes use `engine.begin()` transaction boundaries. The solution writer replaces generated assignments using `TPlanPersonalKommtGeht` and existing plan/personnel/shift context. Wishes, availability, minimum staffing and weights have separate writers. Transactions roll back on failure; independent input acceptance, exact publication/clear scope and connected write verification are still unfinished.

Generation also writes compatibility JSON to the shared runtime data directory for feasible results. Those filesystem exports are separate from SQL publication and from the pending portable bundle contract. See [limitations](../validation/index.md) before treating a result as accepted or published.
