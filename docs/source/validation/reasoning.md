# Reasoning and requirements

For reviewers assessing why the scheduling model and its evaluation fit the task. The [solver reference](../architecture/solver.md) describes how the rules are implemented; [evidence and limitations](index.md#solver-and-schedule-check) records what has been run. Nothing here is a legal-compliance assessment.

## Problem and agreed planning scope

The assignment asks for monthly hospital rosters that meet minimum staffing by qualification and shift, keep approved absences and free days, stay within ±7.67 hours of each employee's monthly target, and respect working-time law and occupational-science findings. This project plans two fictional stations and their shared jumper pool for January to June 2026: one run per full month with both stations selected. The population is adult; no employee wishes and no special capabilities (such as rounds or night-watch roles) are part of the examples. Qualifications are Fachkraft, Hilfskraft, Azubi and MFA; they never substitute for each other.

## Requirements, sources and assumptions

| Requirement                                        | Source                                                   | Assumption made                                                                                      |
| -------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Minimum staffing per station, shift, qualification | Chair's minimum-staffing table, profiles 85 and 79       | NRW public holidays use the weekend row; blank cells mean no minimum                                 |
| Monthly balance ±7.67 h                            | Problem statement                                        | 460 whole minutes; credits are verified TimeOffice absence credits, counted once                     |
| Daily work, breaks, rest                           | [ArbZG](https://www.gesetze-im-internet.de/arbzg/) §§3–5 | Ordinary adult baseline: no hospital rest reduction and no collective/church (AVR) exception applied |
| Night work average                                 | ArbZG §6(2)                                              | Employees with night duties average over the calendar month                                          |
| Sunday and holiday replacement rest                | ArbZG §11(3)                                             | A replacement day is a duty-free Werktag within two weeks (Sunday) or eight weeks (holiday)          |
| Night blocks and recovery                          | BAuA night- and shift-work guidance                      | Adopted as project policy: at most three nights in a row, 48 hours after the final night             |

AVR applicability, its annexes and any employer agreement are unconfirmed, so they supply no exception. The BAuA numbers are recommendations made binding for this project, not standalone statutory limits.

## Hard rules and soft priorities

Hard rules are what a schedule must satisfy to be usable: staffing, eligibility by dated membership and qualification, one duty per day, availability, monthly balance, work and breaks, work average, rest, consecutive nights, night recovery and replacement rest. Soft priorities rank schedules that satisfy them: health events first, then the monthly balance, then additional intermediate duties. Earlier legacy objectives (assignment-count balancing, overtime-only penalties, block-length and weekend rewards, wish scores, intermediate-shift hierarchy) were removed because they were arbitrary or duplicated a hard rule.

## Modeling choices and alternatives

Rules use actual duty times instead of shift-code pairs: a late shift ending at 21:00 followed by an early shift at 05:55 fails the eleven-hour rest because of the 8 h 55 min gap, not because of its codes. Breaks come from the evidenced work segments of each shift, because a paid-time deduction cannot show where a break lies. Month boundaries are explicit trusted context with a declared coverage instead of assuming free days at the month's edges. A single weighted objective with dominance weights replaces several solver passes; it is exact and needs no optimization framework. In-month fixed duties are not supported, because no plan reconciliation is part of the scope.

## Objective units and trade-offs

Health events are counts, the balance is minutes and the intermediate reward is a count of duties. The weights make the order strict: avoiding one health event is worth more than any balance improvement, and one minute of balance is worth more than any number of extra intermediate duties. Consequently an extra intermediate duty is planned only when it does not worsen anyone's balance, and a balance improvement never buys a backward shift step. The automated solver tests check both boundaries with schedules that differ in one tier.

## Independent acceptance and evaluation

`check_schedule` evaluates every hard rule from the actual assignments, dataset and context, not from solver variables. It reports findings, not-assessed obligations with their exact windows, and the three raw scores. A schedule is accepted only if no rule is violated and every promised check had its input. Missing preceding context blocks acceptance; obligations beyond the month or the year are listed as not assessed and limit the claim. The solver's objective value equals the weighted total of the scores recomputed by the check, which cross-validates both. The prepared months are evaluated with live runs; see [evidence](index.md#solver-and-schedule-check).

## Known limits and future work

- Annual free Sundays and the 24-week average outside night work need longer history and are not assessed.
- A month's check matches replacement days only for its own Sundays and holidays; claims across months are validated with the six-month sequence.
- Time-limited runs return feasible schedules with a large reported gap; the bound is weak, the schedule itself is checked.
- Minors, other employment regimes and employer-specific agreements would need their own rule sources.
