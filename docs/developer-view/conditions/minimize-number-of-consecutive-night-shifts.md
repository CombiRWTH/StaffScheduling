--8<--
user-view/list-of-conditions.md:min-num-of-cons-night-shifts
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/objectives/minimize_consecutive_night_shifts.py"
# Penalize longer consecutive night shift blocks with exponentially increasing penalties
for length, var in night_block_vars:
    # 2 nights: mild penalty; 4+ nights: steep exponential penalty
    multiplier = 2 ** (length - 1)
    penalties.append(
        Penalty(
            objective_id=self.id,
            name=f"consecutive_nights_length_{length}",
            expression=var,
            multiplier=multiplier,
        )
    )
```

For each employee, the solver tracks consecutive night shift streaks. Penalties scale exponentially with block length to heavily discourage assigning 4, 5, or more night shifts in a row.
