# Balance Generated Assignments (Load Balancing)

This objective minimizes the maximum number of generated shifts assigned to any single employee, promoting a balanced workload across the ward staff.

---

### Clinical Motivation

When staff scheduling problems are solved, the optimizer could theoretically fulfill all staffing quotas by overburdening a small group of flexible employees with excessive shifts while leaving others underutilized.

This objective introduces a **minimax fairness balance**: it computes the total number of generated shifts per employee and minimizes the peak maximum, distributing required shifts as evenly as possible among all available personnel.

---

### Implementation in CP-SAT

```python title="src/scheduling/solver/cp_sat/objectives/temporary_balance_generated_assignments.py"
# 1. Count generated assignments per employee
generated_counts = [sum(variables) for variables in variables_by_employee.values()]

# 2. Define maximum peak variable
max_generated_assignments = ctx.model.new_int_var(
    0,
    len(ctx.assignment_variables),
    "temporary_balance_generated_assignments__max_per_employee",
)

# 3. Enforce max_generated_assignments == max(generated_counts)
ctx.model.add_max_equality(
    max_generated_assignments,
    generated_counts,
)

# 4. Minimize peak penalty
return (
    Penalty(
        objective_id=self.id,
        name="max_generated_assignments_per_employee",
        expression=max_generated_assignments,
    ),
)
```

---

### Audit & Inspection

During the post-solve audit, the system inspects the distribution of assignments across all active employees and records an informational diagnostic finding with the maximum workload observed.
