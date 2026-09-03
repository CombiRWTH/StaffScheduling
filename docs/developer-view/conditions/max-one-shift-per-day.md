--8<--
user-view/list-of-conditions.md:user-max-one-shift-per-day
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/constraints/one_assignment_per_day.py"
# Enforce at most one shift assignment per employee and calendar date
for (employee_id, assignment_date), variables in vars_by_employee_date.items():
    ctx.model.add(sum(variables) <= 1).with_name(f"one_assignment_emp_{employee_id}_{assignment_date:%Y%m%d}")
```
