--8<--
user-view/list-of-conditions.md:min-number-of-staff-per-shift
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/constraints/minimum_staffing.py"
# For each date, shift, and qualification level, enforce exact staffing demand
ctx.model.add(sum(candidate_variables) == requirement.required_count).with_name(
    _constraint_name(requirement)
)
```

For every planning date, shift, and required qualification role (`StaffLevel.PROFESSIONAL`, `ASSISTANT`, `TRAINEE`), the solver collects all eligible assignment variables and constrains their sum to equal `requirement.required_count`.
