# Solver and schedule check

One run solves exactly one full calendar month for the selected stations with OR-Tools CP-SAT. Every schedule it finds is then judged by an independent schedule check. Solver status, schedule check and job state are three separate results. The rules and their sources are explained in [reasoning and requirements](../validation/reasoning.md); executed evidence is in [current limitations](../validation/index.md#solver-and-schedule-check).

## Modules

| Module                 | Responsibility                                                                                                                           |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `domain/duty.py`       | `duty_times(date, shift)`: a duty's Europe/Berlin start, end and work segments as UTC instants                                           |
| `domain/rules.py`      | `RulePolicy`: every hard-rule parameter, the context days a month needs and which dates need replacement rest                            |
| `domain/acceptance.py` | `check_schedule(dataset, assignments)`: every hard rule and the three objective scores, from actual assignments                          |
| `solver/model/`        | `build_model(dataset)`: the candidates, each rule of `HARD_RULES` and the tiers of `OBJECTIVES`; see [model structure](#model-structure) |
| `solver/service.py`    | `SolverService.solve(dataset, timeout)`: build, validate, solve, extract the schedule and run `check_schedule` on it                     |
| `solver/generation.py` | The transient generation job around one solve; see [API generation](api.md#generation)                                                   |

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

## Model structure

`build_model` is the only entry point; `SolverService` and the tests call nothing else. Inside `solver/model/`, each rule and each objective term is one function, listed in one tuple, so it can be read, changed and tested on its own:

| File             | Holds                                                                                                                                                                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `candidates.py`  | `CandidateModel`: the CP-SAT model, one variable per candidate, every employee's `timelines` of candidate and fixed context `Slot`s ordered by start, the diagnostics, and helpers for limits over slots (`at_most`), monthly balances and 0/1 logic (`logical_and`, `and_not`) |
| `constraints.py` | One function `(model) -> None` per hard rule and `HARD_RULES`, their order                                                                                                                                                                                                      |
| `objectives.py`  | One function `(model) -> Term` per objective term, `OBJECTIVES` (the tiers, highest priority first, each naming its terms) and `set_objective`, which derives the weights and sets the objective                                                                                |

Availability and the work and break pattern of a single duty decide which candidates exist, in `candidates.py`; they are not constraints. Staffing and the balance band come last in `HARD_RULES`, because their diagnostics and balances skip the candidates that context duties rule out in the rules before them.

## Adding or changing a hard rule

Change the parameter in `RulePolicy`, or the rule in both places. In the model, a rule about a single duty filters candidates in `candidates.py`; any other rule is a function in `constraints.py` added to `HARD_RULES`. Use `model.at_most` for limits over slots, so context duties count as worked and the staffing diagnostic sees what they rule out. Implement the rule again, independently, in `domain/acceptance.py` with its own `Rule` member. Add a discriminating boundary example to `api/tests/test_schedule_check.py` and, where the model encodes it, a production solve to `api/tests/test_solver.py`. Keep domain inputs independent of TimeOffice and run the [shared checks](../development/checks.md).

## Adding an objective

An objective is a term the solver minimizes (or, as a reward, maximizes) after every hard rule holds. Health events, for example, are one tier of two terms, six-day windows and backward transitions, both counts weighted alike.

1. **Define the score.** State what is counted, its unit (a count of events or duties, or minutes), whether it is a penalty or a reward, and its priority among the tiers. A new concern of the same unit and priority as an existing tier becomes a term of that tier; otherwise it is a new tier. Record the reasoning in [reasoning and requirements](../validation/reasoning.md).
2. **Score it independently.** Add the field to `ScheduleScores` in `domain/acceptance.py` and compute it in the check's `scores` from assignments and context alone, never from solver variables. A tier of several terms is a computed field, like `health_events`. The [portable scoring contract](../validation/examples.md#interpret-objectives-and-solver-settings) describes how scores, weights and the objective value relate in every result.
3. **Model the term.** Add a function `(model: CandidateModel) -> Term` to `objectives.py`. Its expression must equal the check's score exactly for every schedule that keeps the hard rules: not a bound or a relaxation, or the reported objective stops matching the check. Loop over `model.timelines` per employee; fixed context slots count as worked (`slot.expr` is 1). `Term.bound` is the largest value the expression can take in this month; it should be tight, because it sets the weights above it.
4. **Place it.** Add the function to a tier's terms in `OBJECTIVES`, or add a new `Tier` at its priority, named exactly like its new `ObjectiveWeights` field in `solver/models.py`. Mark a reward with `reward=True`.
5. **Check the weights.** `set_objective` gives the lowest tier weight 1 and every higher tier 1 more than the largest weighted total of all tiers below it, so one unit of a higher tier always outweighs them. It raises `ValueError` when the largest possible total could reach 2⁵³, the limit of exact objective values. Build the largest example month and confirm the weights stay well below it.
6. **Report it.** The weights appear in `configuration.weights` and the score in `check.scores` of every API response and portable `result.json`. Run the API tests once to rewrite the published [result schema](../validation/schema/result.schema.json) and commit it; update `webapp/src/lib/types.ts`, the review's **Technische Details**, the [objective section](#objective) above and the [example file reference](../validation/examples.md). Bundles from before the change no longer re-check identically, so regenerate committed examples.
7. **Verify it.** Add a boundary example of the score to `api/tests/test_schedule_check.py`. In `api/tests/test_solver.py`, extend `weighted_total` so every solve still proves objective value = checked weighted total, and add two-schedule boundary tests against the neighbouring tiers, like the existing ones for health over balance and balance over intermediate duties: one unit of the higher tier must outweigh the most the lower one can change. `test_objective_tiers_are_the_reported_weights_and_scores_in_priority_order` fails until the tier name matches its weight and score fields. [Testing](../development/testing.md#unit-responsibilities) lists what both test files already cover.
