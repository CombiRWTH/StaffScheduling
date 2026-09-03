--8<--
user-view/list-of-conditions.md:rotate-shifts-forwards
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/objectives/rotate_shits_foward.py"
# Penalize backward shift transitions (Late -> Early, Night -> Late)
# and reward forward shift rotations (Early -> Late -> Night)
for (employee_id, date), var in backward_rotation_vars.items():
    penalties.append(
        Penalty(
            objective_id=self.id,
            name="backward_shift_rotation",
            expression=var,
            multiplier=1,
        )
    )
```

Chronobiological studies show that rotating shifts clockwise (forward in time: Early $\rightarrow$ Late $\rightarrow$ Night) respects circadian rhythms and minimizes sleep disruption. This objective penalizes backward transitions across consecutive working days.
