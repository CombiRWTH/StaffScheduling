# Lexicographic staged objective instead of derived weights

The solver optimizes the objective tiers of `OBJECTIVES` one CP-SAT stage at a time, in priority order: gaps, health events, station transfers, wish cost, balance deviation, surplus intermediate duties. Each stage optimizes its tier, then fixes the value it reached (`≤`, or `≥` for a reward) and hands its schedule to the next stage as a hint. One unit of a higher tier therefore can never be traded for any change in lower tiers, and no tier needs a weight. The tier expressions are exact for every schedule, so each stage's value equals the score that the independent schedule check recomputes. The requested timeout is the total: each stage gets the remaining time divided by the stages left, so a stage that proves its optimum early passes its time on.

## Considered Options

- **One weighted sum with derived dominance weights** (the previous model). Rejected: each weight must exceed the largest possible total of all lower tiers, and CP-SAT reports objective values as doubles, exact only below 2⁵³. January's three earlier tiers already reached about 2.4·10¹¹; gaps and wishes push that to about 3·10¹⁷, so the build would fail for real months.
- **Hand-chosen weights.** Rejected: they cannot guarantee the priority order, contradict "no wish weights", and make reported values depend on tuning.
- **Fewer tiers or one combined score.** Rejected: gaps, health, station transfers, wishes and account balance have different units and a decided priority order.

## Consequences

- A time-limited stage reports `feasible` with its proven bound. A later stage may still improve that tier within the fixed limit, so stage values are read from the final schedule.
- Only the first stage can be `infeasible` or `unknown`. A later stage that finds nothing better keeps the previous schedule. The solution is `optimal` only if every stage is.
- The top tier gets only part of the time. Live January needed 300 s instead of 120 s for good health scores.
- Results report every stage instead of weights and one objective value. Portable format version 2 replaced version 1, and older bundles are not re-checked.
- Reordering tiers is a code change to `OBJECTIVES`.
