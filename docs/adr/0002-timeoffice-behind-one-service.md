# Keep TimeOffice behind one service of plain query functions

TimeOffice is an external roster database whose schema and terms we do not control, and it is to be replaced by another database later. The API reaches it only through `TimeOfficeService`, which takes and returns canonical domain models; routes depend on a small consumer-owned protocol, not on TimeOffice. Inside the package each SELECT is one function that returns domain models and owns its source-code translation and source checks, while cross-entity completeness rules live in the domain.

## Considered Options

- **Reader classes, row models and separate mappers per table** (the imported structure). Rejected: each layer mapped one-to-one onto the next, and the row models re-checked what the domain models already check.
- **An ORM or repository layer.** Rejected: the adapter only runs a few fixed, read-only SELECTs against a schema we do not own; mapped entities would expose TimeOffice structure without removing any SQL.

## Consequences

A replacement database implements the same protocol. If a second implementation appears, the orchestration in `inspect_employees` (scoping before reading accounts and restrictions) should move into the domain, so it is not duplicated.
