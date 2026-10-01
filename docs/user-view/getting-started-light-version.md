# Working without TimeOffice access

Install dependencies using the shared [installation guide](../installation.md). Local solver tests construct canonical input models without connecting to SQL Server; run them from `api/` with `uv run python -m pytest -m integration`.

Historical JSON inputs remain under `api/cases/` and `webapp/cases/`, with archived examples under `api/legacy/`. They use the [legacy JSON formats](../developer-view/json-dataformat.md) and [webapp file formats](../webapp/underlying_data.md). The API and CLI currently fetch canonical solve inputs from TimeOffice; importing an old JSON case into the UI does not provide a verified offline solve.

The webapp can display imported files and views without live database access, but generation, progress and publication have [known integration gaps](../webapp/solver-integration.md). An independent portable input/result workflow is still being implemented. These historical files are not the required validated six-month example exports.
