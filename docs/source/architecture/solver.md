# Solver

This reference describes inspected source definitions. Connected database behavior and complete user workflows require separate acceptance evidence; see [current limitations](../validation/index.md).

`SolverService` builds and runs an OR-Tools CP-SAT model from a validated `SchedulingDataset`. It extracts generated assignments, evaluates the configured component audits and returns a solution status, diagnostics and audit findings.

## Model and configuration

`solver/cp_sat/context.py` builds indexes. `variables.py` creates eligible Boolean assignment variables indexed by employee, unit, date, shift and staffing level. `builder.py` applies registered constraints and collects weighted penalties to minimize. `solver/config.py` determines enabled components, parameters and internal weights. Required constraints cannot be disabled through this configuration.

The current builder registers these hard-constraint components:

- Minimum staffing.
- Recovery after a night-shift phase.
- Rounds in early shifts.
- Availability constraints.
- Intermediate-shift hierarchy.
- At most one assignment per day.
- Target working time.

Its objectives cover assignment balance, overtime, consecutive workdays, preferred block length, forward rotation, alternating free weekends, wishes/fairness, night-phase recovery, free days near weekends and consecutive night shifts. Their registration documents what the current model runs; it does not establish independent correctness or complete legal-policy coverage.

## Execution and result

`inspection.py` checks CP-SAT model validity before search. `SolverService` maps OR-Tools results to `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `MODEL_INVALID` or `UNKNOWN`. Only feasible/optimal results yield extracted assignments and component audits. The audit includes imported existing assignments alongside generated work.

A feasible model satisfies the implemented model, which may differ from the complete intended policy. The audit reuses constraint/objective implementations. Independent acceptance and policy correction remain pending, and preferred-block-length/forward-rotation tests currently fail. See [limitations](../validation/index.md#quality-gates).

## Settings

| Environment variable         | Default | Purpose                                            |
| ---------------------------- | ------- | -------------------------------------------------- |
| `SOLVER_MAX_TIME_SECONDS`    | `30`    | Default search limit for direct solver-service use |
| `SOLVER_NUM_SEARCH_WORKERS`  | unset   | Leave OR-Tools worker selection unchanged          |
| `SOLVER_RANDOM_SEED`         | unset   | Optional search seed                               |
| `SOLVER_LOG_SEARCH_PROGRESS` | `false` | Enable solver progress logs                        |

The engine is currently exercised only by its unit tests; no API route invokes it until the generation slice reconnects it. A fixed seed alone does not guarantee reproducibility with parallel search. Set settings in root `.env` for Compose and recreate the API after changes.

## Changing a rule

Read the relevant component, callers and focused tests first. Constraints implement model construction and audit; objectives return penalty expressions and audit findings. Register actual new components in `cp_sat/builder.py` and `solver/config.py`, and exercise the behavior in the corresponding `api/tests/cp/` area. Keep domain inputs independent of TimeOffice. Run focused tests and the shared checks described in [code quality](../development/checks.md).
