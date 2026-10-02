# TimeOffice adapter

This reference describes inspected source definitions. Connected database behavior and complete user workflows require separate acceptance evidence; see [current limitations](../validation/index.md).

`api/app/timeoffice/` owns the application's Microsoft SQL Server integration. `TimeOfficeService` coordinates read-only queries and their translation into canonical models. The solver depends on the [domain model](domain.md), not the database schema.

## Modules

| Path under `api/app/timeoffice/` | Responsibility                                                                                   |
| -------------------------------- | ------------------------------------------------------------------------------------------------ |
| `database.py`                    | SQLAlchemy engine using `mssql+pyodbc`                                                           |
| `facts.py`                       | Reference identifiers, shift mappings and planning status assumptions                            |
| `queries.py`                     | One function per TimeOffice SELECT, returning canonical models with its code/account translation |
| `service.py`                     | `TimeOfficeService`, the package's only public entry point; one connection per call              |

## Connection and schema

Follow [database configuration](../getting-started/installation.md#database-configuration) for `.env` and the password file. Docker includes ODBC Driver 18. `database.py` constructs the SQLAlchemy URL with `Encrypt=yes` and `TrustServerCertificate=no`. Its shared connection boundary checks missing configuration/driver, applies bounded login/query waits, and translates driver failures into safe integration errors for all adapter callers. FastAPI returns these as `503` with `integration`, `stage` and actionable `detail`; liveness remains independent. No connection strings, SQL or raw driver errors are returned.

`just connectivity` runs the explicit diagnostic in the API container. It checks configuration/ODBC/DNS, encrypted login and `SELECT 1`, then disposes the engine. It bypasses all application queries. Offline boundary checks cover missing configuration, missing driver, sanitized login/query failures and a simulated successful diagnostic. The configured external test target did not pass the encrypted connection stage in the latest container run; live schema/workflow acceptance remains outstanding. See [testing](../development/testing.md).

The adapter reads TimeOffice tables including `TPlanungseinheiten`, `TPlanungseinheitenPersonal`, `TPersonal`, `TPlan`, `TDienste`, `TPlanPersonalKommtGeht` and monthly/daily account tables. Actual SQL and join/filter rules are in `queries.py`; this reference does not substitute a copied schema diagram for the database's current schema.

## Read and write boundaries

`TimeOfficeService` is the adapter's whole interface: `get_planning_options` and `inspect_employees` take canonical arguments and return canonical domain models. SQL, source rows and TimeOffice terminology stay private to the package (`app.timeoffice` exports only the service, the unavailable error and the engine factory). Each query function translates its own source codes and checks source-level facts such as missing master rows, duplicate target plans or unmapped codes; cross-entity completeness belongs to `domain/inspection.py`. The API depends on a small `PlanningSource` protocol, so another planning database can replace TimeOffice without touching routes or domain. TimeOffice reductions and fixed reference mappings in `facts.py` remain adapter behavior and must be checked against the chosen data.

The adapter performs no SQL writes and builds no solver dataset. Configuration writes, generation inputs and publication are added later as canonical operations behind the same service.

## Employee inspection evidence

Selection and employee inspection are strictly read-only. They never create tables, nor do they require `TPlanPersonal` or existing work duties in an empty target. Target plans are selected internally by configured status/interval and exact month bounds. Memberships across the configured units determine pool/home context; pool origin alone is never destination eligibility. Missing names, identities, unique targets or complete evidence fail inspection.

Monthly native target/actual reads use the configured account IDs (currently target 1 and actual 55, `Wert2` hours). The adapter converts finite nonnegative hours to integer minutes, retaining explicit zero. Native actual totals are not approved credits; their meaning still needs live verification against the prepared source.

An authorized preparer must explicitly run `api/sql/employee-inspection.sql` once in the declared test database, then supply `dbo.StaffSchedulingEmployeeMonthEvidence`. Reads never provision it. The service account needs SELECT, not DDL/write permission for this operation. This slice supplies the schema/read contract; it does not execute setup or claim live source acceptance.

Each row is keyed by positive `employee_id` and first-of-month `planning_month`. Required `credit_details` and `constraints` are JSON arrays; `source` names the verified complete monthly declaration. Credit objects contain `date`, `minutes`, `kind` (`approved_absence` or `trusted_work`) and `source`. Additional constraints use the canonical Availability fields: employee ID, full date, availability type, optional allowed `shift_ids`, reason and source. Native absences are loaded separately and retain their reason. Explicit empty arrays declare verified zero credits/no additional constraints; they are never installed as defaults. Missing declarations/accounts, duplicate credits, unknown identities/shifts, mismatched month dates and ambiguous home origin reject the complete inspection.

Do not copy polluted actual roster totals into this table, fabricate balancing credits or declare constraints complete without reviewing applicable contracts/source absences. Prepared-data verification must establish native account semantics, completeness and provenance before live use. Generation is not connected to the API; solver input, correction and accepted exports remain later gates.
