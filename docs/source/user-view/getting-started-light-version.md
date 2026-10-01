# Working without TimeOffice access

Install dependencies using the shared [installation guide](../installation.md). Local solver tests construct canonical input models without connecting to SQL Server; run them with `just test -m integration`.

Historical case directories are no longer bundled with the services. File-based screens remain temporarily, but API generation requires TimeOffice data. A UI file import is not a verified offline solve.

The webapp can display imported files and views without live database access, but generation, progress and publication have [known integration gaps](../webapp/solver-integration.md). An independent portable input/result workflow is still being implemented. These historical files are not the required validated six-month example exports.
