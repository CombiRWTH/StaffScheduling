# Solver and schedule check

One run solves exactly one full calendar month for the selected stations with OR-Tools CP-SAT. Every schedule it finds is then judged by an independent schedule check. Solver status, schedule check and job state are three separate results. The rules and their sources are explained in [reasoning and requirements](../validation/reasoning.md); executed evidence is in [current limitations](../validation/index.md#solver-and-schedule-check).

## Modules

| Module                 | Responsibility                                                                                                       |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `domain/duty.py`       | `duty_times(date, shift)`: a duty's Europe/Berlin start, end and work segments as UTC instants                       |
| `domain/rules.py`      | `RulePolicy`: every hard-rule parameter, the context days a month needs and which dates need replacement rest        |
| `domain/acceptance.py` | `check_schedule(dataset, assignments)`: every hard rule and the three objective scores, from actual assignments      |
| `solver/model.py`      | `build_model(dataset)`: candidate variables, every hard rule as constraints and the weighted objective               |
| `solver/service.py`    | `SolverService.solve(dataset, timeout)`: build, validate, solve, extract the schedule and run `check_schedule` on it |
| `solver/generation.py` | The transient generation job around one solve; see [API generation](api.md#generation)                               |

`check_schedule` never sees solver variables. It recomputes duty times, accounts and sequences from the `SchedulingDataset` and the assignments, so it judges a solver result and any other assignment list alike. Solver and check implement every rule separately; they share only `RulePolicy` and the duty times of `duty.py`, so an error in one implementation shows as a disagreement with the other.

## Candidates and context

The model has one Boolean per candidate duty: employee, station, start date, shift and the qualification it is credited as. A candidate exists when the employee has an active membership at the station on that date with that qualification, no approved availability forbids the duty and the shift's own work and break pattern is allowed on that date. A candidate that the employee's trusted context duties alone rule out (a rest, night-run or recovery conflict whatever else is chosen) is fixed to zero by those constraints and not counted as possible in the staffing diagnostic. Several memberships give several candidates, of which at most one can be chosen; the chosen one is the assignment's `staff_level`. Jumper pools are origin context and never destinations.

`SchedulingDataset.context` holds trusted duties outside the month with explicit coverage (`covered_from`, `covered_until`) and the approved availability of the first date after the month. Inside the coverage a date without a duty is free; outside it nothing is known. A month needs the 5 dates before it and checks the 3 dates after it (`preceding_context_days`, `following_context_days`). Context constrains rest, nights, recovery, replacement rest, six-day windows and shift order across the month boundary. It never counts towards demand or monthly accounts. Duties inside the month cannot be supplied as fixed input; the adapter refuses them.

## Hard rules

All parameters are in `RulePolicy` and reported with every run.

| Rule               | Model                                                                                                                                                                 |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Staffing           | For every dated demand row (station, shift, qualification): candidates credited with that qualification ≥ the required count. Zero or omitted means no minimum.       |
| One duty per day   | At most one candidate per employee and start date, across all stations and qualifications                                                                             |
| Availability       | Blocking entries forbid every duty touching the date; allowed-shift entries narrow each other; no night before an approved vacation or free day                       |
| Monthly balance    | Generated paid minutes + verified credits − target ∈ [−460, 460] minutes for every employee, including employees without any possible duty                            |
| Work and breaks    | Per duty, from its segments: at most 10 hours of work; over 6 h at least 30 and over 9 h at least 45 minutes of break in parts of ≥ 15 minutes; ≤ 6 h without a break |
| Work average       | Every employee's work in the month stays ≤ 8 hours × Werktage (Mon–Sat, not a holiday), so duties up to 10 hours are always balanced within the month                 |
| Rest               | At least 11 elapsed hours between the end and the next start of any two duties, including context                                                                     |
| Consecutive nights | At most three night duties on consecutive dates, including context                                                                                                    |
| Night recovery     | No duty starts within 48 elapsed hours after the end of the final night of a block                                                                                    |
| Replacement rest   | Each worked Sunday or Werktag holiday of the month gets its own duty-free Werktag of the same month within ±13 days (Sunday) or ±55 days (holiday)                    |

A duty touches a date when its interval overlaps that local day from 00:00 to 24:00, so a Saturday night counts as Sunday work. Elapsed time follows daylight-saving changes; paid minutes do not. A shift time that a clock change skips or repeats is rejected when the input is built.

## Objective

After the hard rules, the model minimizes three tiers in order:

1. **Health events**: fully worked six-day windows (a window counts on its last day, inside the month; seven days in a row are two windows) plus backward steps between successive early, late and night duties (early → late → night is forward; off days do not reset the comparison; intermediate and other duties have no position). The first ranked duty of the month is compared with the last ranked duty of the five preceding context days, if any.
2. **Balance deviation**: the sum of every employee's absolute monthly balance, in minutes.
3. **Surplus intermediate duties**, as a reward: intermediate duties beyond the required ones.

The weighted total is `health × W1 + balance × W2 − surplus × W3`. Weights are derived per run from the input's bounds so that one unit of a higher tier outweighs any possible change of all lower tiers: `W3 = 1`, `W2 = U3 + 1`, `W1 = W2 × U2 + U3 + 1`, with `U3` the employee-days with an intermediate candidate and `U2 = 460 ×` employees. The build fails if the largest possible total could reach 2⁵³, so reported values stay exact. The tier encodings are exact (not bounds), so the solver's objective value equals the weighted total of the scores that `check_schedule` recomputes. The live January example uses `W1 = 41 114 528`, `W2 = 1 568`, `W3 = 1`.

## Result

`Solution` contains:

- `status`: `optimal`, `feasible` (the time limit ended the search), `infeasible` (proven), `unknown` (neither a schedule nor a proof in time) or `model_invalid`.
- `configuration`: the `RulePolicy`, the weights, timeout, search workers and seed.
- `wall_time_seconds` and `diagnostics`.
- With a found schedule only: `assignments`, `objective` (`value`, `best_bound`, `relative_gap`) and `check`.

`diagnostics` name causes the build can see, such as demand without enough candidates (`staffing.too_few_candidates`, counted after availability and context conflicts), an employee who cannot reach the balance band without duties (`balance.unreachable`) or a shift whose pattern breaks the daily rules. A `feasible` schedule after a time limit can be improved by up to the reported gap; a large gap means the bound is weak, not that the schedule breaks a rule.

`check` has `status` `accepted` (every promised rule checked and kept), `rejected` (a hard-rule finding) or `incomplete` (no finding, but a promised check lacks input), plus `findings`, `not_assessed` and `scores`. Not-assessed items give the rule, the exact date window and the reason, and say whether they block acceptance:

| Not assessed                                                                | Blocking | Why                                                                                                                  |
| --------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------- |
| Rest, nights, recovery and scores at the month start without 5 context days | yes      | A six-day window ending on the first date reaches five days back; a night three days earlier still reaches the month |
| Rest, nights and recovery after the month without 3 following context days  | no       | The next month's run checks them with this schedule as its preceding context                                         |
| Annual free Sundays                                                         | no       | Needs the whole year                                                                                                 |

Replacement rest and the work average are decided within the month, so they never depend on other months and no replacement day is claimed twice.

## Settings

| Environment variable         | Default | Purpose                                   |
| ---------------------------- | ------- | ----------------------------------------- |
| `SOLVER_MAX_TIME_SECONDS`    | `30`    | Search limit when a caller passes none    |
| `SOLVER_NUM_SEARCH_WORKERS`  | unset   | Leave OR-Tools worker selection unchanged |
| `SOLVER_RANDOM_SEED`         | unset   | Optional search seed                      |
| `SOLVER_LOG_SEARCH_PROGRESS` | `false` | Enable solver progress logs               |

`POST /generation` passes the requested `timeout_seconds` as the search limit; the other settings apply unchanged and are reported in `configuration`. A fixed seed alone does not make parallel search reproducible. Set settings in root `.env` for Compose and recreate the API after changes.

## Changing a rule

Change the parameter in `RulePolicy`, or the rule in both places: as a constraint in `solver/model.py` and independently in `domain/acceptance.py`. Add a discriminating boundary example to `api/tests/test_schedule_check.py` and, where the model encodes it, a production solve to `api/tests/test_solver.py`. Keep domain inputs independent of TimeOffice and run the [shared checks](../development/checks.md).
