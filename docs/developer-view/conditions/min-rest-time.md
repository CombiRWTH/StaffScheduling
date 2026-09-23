--8<--
user-view/list-of-conditions.md:min-rest-time
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/constraints/min_rest_time.py"
# Prevent a Late shift today from being followed by an Early shift tomorrow (minimum 11-hour rest time)
constraint = ctx.model.add(sum_late + sum_early <= 1)
constraint.with_name(_constraint_name(employee_id, date))
```

Under the German Working Hours Act (*Arbeitszeitgesetz*), employees must receive an uninterrupted rest period of at least 11 hours between shifts. In standard hospital shift rotations, working a Late shift (ending around 21:00 or 22:00) followed immediately by an Early shift (starting around 06:00) yields only an 8–9 hour rest interval. The constraint strictly forbids this transition: `sum(late_today) + sum(early_tomorrow) <= 1`.
