# Keep generation jobs in memory of one API process

A generation runs in a background thread of the API process. One process-wide lock admits a single run, and the latest job (running or finished) is kept in memory only; `GET /generation` reports it. The input is read and validated before the job starts, so invalid or incomplete input never becomes a job.

## Considered Options

- **A job queue or database-backed job table.** Rejected: one staff administrator plans one month at a time, and results are reviewed right after the run. A queue, worker service and job history would add infrastructure without a user need.
- **Validating inside the background job.** Rejected: invalid requests and runtime failures would both appear as failed jobs. Reading the input first returns `422`/`409`/`503` before anything starts.
- **Keeping every job by ID.** Rejected: only the latest job is shown, and a second run cannot start while one is running.

## Consequences

The API must run as a single process: a second process would have its own lock and jobs. A restart, including a development source reload, forgets results and does not resume a running solve. Generated results are drafts; keeping or publishing them needs its own explicit step.
