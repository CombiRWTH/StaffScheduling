--8<--
user-view/list-of-conditions.md:preferred-block-length
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/objectives/preferred_block_length.py"
# Penalize shift streaks that deviate from the optimal ergonomic block length (e.g. 3-4 days)
for length, var in block_length_vars:
    deviation = abs(length - target_block_length)
    penalties.append(
        Penalty(
            objective_id=self.id,
            name=f"block_length_deviation_{length}",
            expression=var,
            multiplier=deviation,
        )
    )
```

Working single isolated shifts or overly long streaks causes circadian fatigue. This objective penalizes blocks that deviate from the station's target block length (e.g. 3–4 days of the same shift type).
