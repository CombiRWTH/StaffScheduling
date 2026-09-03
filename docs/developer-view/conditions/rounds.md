--8<--
user-view/list-of-conditions.md:rounds
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/constraints/rounds_in_early_shift.py"
# For each weekday early shift, require at least one nurse qualified for rounds (Visiten)
ctx.model.add(sum(vars_for_round) >= 1).with_name(_constraint_name(date))
```

On hospital wards, doctors' rounds (*Visiten*) occur during early shifts on weekdays. These rounds require a qualified nurse who knows the patients and station procedures. The constraint gathers the early shift variables of all nurses with round permissions and enforces that at least one of them is on duty: `sum(vars_for_round) >= 1`.
