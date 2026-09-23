--8<--
user-view/list-of-conditions.md:target-working-time
--8<--

### Implemented using Google's OR-Tools

```python title="src/scheduling/solver/cp_sat/constraints/target_working_time.py"
# Enforce that total generated working minutes fall within tolerance of monthly target
ctx.model.add(total_working_minutes <= target_max).with_name(
    f"target_time_upper_emp_{employee_id}"
)
ctx.model.add(total_working_minutes >= target_min).with_name(
    f"target_time_lower_emp_{employee_id}"
)
```

For each employee, the solver calculates the sum of worked shift minutes (`sum(shift.duration_minutes * var)`). This is bounded within `[target_min, target_max]` (typically within ±1 shift duration of the employee's contracted hours). Deviations from the exact target are additionally penalized by the [Minimize Overtime and Undertime](./minimize-overtime-and-undertime.md) objective.
