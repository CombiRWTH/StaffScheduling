# Reasoning and requirements

For reviewers assessing why the scheduling model and its evaluation fit the task. The [solver reference](../architecture/solver.md) describes how the rules are implemented; [evidence and limitations](index.md#solver-and-schedule-check) records what has been run. Nothing here is a legal-compliance assessment.

## Problem and agreed planning scope

The assignment asks for monthly hospital rosters that meet minimum staffing by qualification and shift, keep approved absences and free days, stay within ±7.67 hours of each employee's monthly target, and respect working-time law and occupational-science findings. This project plans two stations of the TimeOffice test database and their jumper pool for January to June 2026: one run per full month with both stations selected. The population is adult; the examples carry a small demonstration set of employee wishes, including jumper pool employees, and no special capabilities (such as rounds or night-watch roles). Qualifications are Fachkraft, Hilfskraft, Azubi and MFA; they never substitute for each other.

## Requirements, sources and assumptions

| Requirement                                        | Source                                                   | Assumption made                                                                                      |
| -------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Minimum staffing per station, shift, qualification | Chair's minimum-staffing table, keys 77 and 79           | NRW holidays use the weekend row; professionals as listed, other levels sized near the real staff    |
| Monthly balance ±7.67 h                            | Problem statement                                        | 460 whole minutes; credits are verified TimeOffice absence credits, counted once                     |
| Daily work, breaks, rest                           | [ArbZG](https://www.gesetze-im-internet.de/arbzg/) §§3–5 | Ordinary adult baseline: no hospital rest reduction and no collective/church (AVR) exception applied |
| Work average for duties up to 10 h                 | ArbZG §3, §6(2)                                          | Every month is its own compensation period: work ≤ 8 h × Werktage, for night and other workers alike |
| Sunday and holiday replacement rest                | ArbZG §11(3)                                             | A duty-free Werktag of the same month within two weeks (Sunday) or eight weeks (holiday)             |
| Night blocks and recovery                          | BAuA night- and shift-work guidance                      | Adopted as project policy: at most three nights in a row, 48 hours after the final night             |
| Employee wishes, jumper pool included              | Course goal; the reference team's fair-preference model  | Wishes never bind; one strike per wish, convex cost per employee                                     |

AVR applicability, its annexes and any employer agreement are unconfirmed, so they supply no exception. The BAuA numbers are recommendations made binding for this project, not standalone statutory limits.

## Hard rules and soft priorities

Hard rules are what a schedule must satisfy to be usable: staffing (or a declared gap), eligibility by dated membership and qualification, one duty per day, availability, monthly balance, work and breaks, work average, rest, consecutive nights, night recovery and replacement rest. Soft priorities rank schedules that satisfy them, highest first:

1. **Gaps.** Staffing is the only hard rule that may be relaxed, and only by a gap: an unfilled required slot reported next to the assignments, so the hospital can request guest staff instead of receiving no schedule at all. Every other rule stays hard, so an honest `infeasible` remains possible. As the top tier, a schedule without gaps always wins where one exists.
2. **Health events.** Health beats preference: no wish is granted at the cost of a six-day run or a backward shift step.
3. **Station transfers.** Working at another station is allowed in general: a station member may work at another station through a replacement membership (Ersatz), and the jumper pool exists for it. A station member's duty at another station is counted and minimized, so the jumper pool is preferred and an organisational transfer is never made merely to grant a wish. Jumper pool duties never count.
4. **Wishes**, fairly. A wish beats balance minutes inside the hard ±460-minute band.
5. **Monthly balance deviation**, in minutes.
6. **Additional intermediate duties**, as a reward.

Earlier legacy objectives (assignment-count balancing, overtime-only penalties, block-length and weekend rewards, weighted wish scores, intermediate-shift hierarchy) were removed because they were arbitrary or duplicated a hard rule.

## Modeling choices and alternatives

Rules use actual duty times instead of shift-code pairs: a late shift ending at 21:00 followed by an early shift at 05:55 fails the eleven-hour rest because of the 8 h 55 min gap, not because of its codes. Breaks come from the evidenced work segments of each shift, because a paid-time deduction cannot show where a break lies. Month boundaries are explicit trusted context with a declared coverage instead of assuming free days at the month's edges. The tiers are solved as lexicographic stages, one CP-SAT solve per tier that fixes the value reached before the next tier is optimized. A single weighted objective with dominance weights was used before; with gaps and wishes its weights would exceed 2⁵³, the limit of exact objective values, for real months (`docs/adr/0010-lexicographic-staged-objective.md`). Averaging and replacement rest are decided within each month: this is stricter than the law's six-month and eight-week periods, but it makes every month's check complete on its own and keeps months from claiming the same replacement day. In-month fixed duties are not supported, because no plan reconciliation is part of the scope.

## Objective units and trade-offs

Gaps are counts of missing employee-shifts, health events and station transfers are counts, the wish cost is a fairness cost of denied wishes, the balance is minutes and the intermediate reward is a count of duties. The stages make the order strict without converting units: one gap more is never traded for any number of health improvements, one health event never for any station transfer, one station transfer never for any wish, one unit of wish cost never for any balance improvement, and one minute of balance never for any number of extra intermediate duties. Consequently an extra intermediate duty is planned only when it does not worsen anyone's balance, and a wish can make an employee work against their balance only inside the hard band. The automated solver tests check every adjacent pair with schedules that differ at the boundary.

## Fair wish satisfaction

The wish tier adopts the fairness approach the reference team chose from the literature: free wishes (free day, free shift) and preferred wishes (preferred day, preferred shift) are scored separately per employee, so a granted preferred day cannot offset a denied free day, and the k-th denied wish of an employee's group costs k³. The convex cost makes two denials for one employee (1 + 8) more expensive than one denial each for two employees (1 + 1), so unavoidable denials are spread. It is encoded as the reference does, with ordered strike indicators per group.

Three defects of the reference implementation are fixed:

- Day wishes counted three strikes and shift wishes one: a wish weight, contrary to the course requirement of no wish weights. Every wish is now one strike.
- Duties were matched to wishes by start date only, so a night starting the evening before did not break a free day. A free day is now broken by any duty touching the date, consistent with the free day of binding availability.
- The configurable objective weights never reached the solver, and the wish term was drowned by a 100-per-minute overtime term. The staged order makes the priority explicit instead.

A wish is one employee and one date at any station; a jumper pool employee's wish counts at both stations. A wish that no schedule could grant (conflicting availability, no station membership, the shift's own pattern, or a trusted context night on a free day) is listed as not grantable and excluded from the cost, so the solver never compensates a denial the planner did not cause. Native TimeOffice wish rows are not read; wishes come from the project's own table. First maximizing the number of granted wishes and only then their fairness, or minimizing the largest number of denials per employee, are possible alternatives; see [limitations](index.md).

## Independent acceptance and evaluation

`check_schedule` evaluates every hard rule from the actual assignments, dataset and context, not from solver variables; solver and check implement each rule separately and share only the rule parameters and duty times. It reports findings, not-assessed obligations with their exact windows, the raw scores and the outcome of every wish. A schedule is accepted only if no rule is violated and every promised check had its input. Missing preceding context blocks acceptance; the boundary to an unplanned next month and the annual free Sundays are listed as not assessed and limit the claim. It recomputes every gap from the assignments: a shortfall not declared exactly as a gap is a staffing violation. Each solver stage's value equals the score recomputed by the check, which cross-validates both. The prepared months are evaluated with live runs; see [evidence](index.md#solver-and-schedule-check).

## Known limits and future work

- Annual free Sundays need the whole year and are not assessed.
- Month-local averaging and replacement rest can reject a schedule that a longer legal period would allow.
- Backward shift steps look back at most five days before the month.
- Time-limited stages return feasible schedules with a weak proven bound; the schedule itself is checked. Each stage gets only a share of the time, so real months need about 300 seconds.
- Minors, other employment regimes and employer-specific agreements would need their own rule sources.
