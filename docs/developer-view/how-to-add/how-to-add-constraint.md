# How to Add a New Constraint

This guide explains how to implement and register a new **hard constraint** in the CP-SAT solver.

---

## Overview

A constraint enforces a non-negotiable rule that every valid schedule must satisfy (such as labor laws, hospital safety policies, or contracted limits). If a constraint cannot be satisfied, the solver marks the problem as **infeasible**.

Every constraint must conform to the **[`Constraint`](https://github.com/CombiRWTH/StaffScheduling/blob/main/src/scheduling/solver/cp_sat/constraint.py)** typing protocol:

```python
class Constraint(Protocol):
    id: ClassVar[str]
    required: ClassVar[bool]

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]: ...

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]: ...
```

* **`add_to_model`:** Translates the business rule into OR-Tools linear constraints on `ctx.model`.
* **`audit`:** Evaluates the solved schedule independently to guarantee correctness and produce diagnostic findings.

---

## Step 1: Create the Constraint File

Create a new file under [`src/scheduling/solver/cp_sat/constraints/`](https://github.com/CombiRWTH/StaffScheduling/blob/main/src/scheduling/solver/cp_sat/constraints/), for example `max_shifts_per_week.py`:

```python
from collections import defaultdict
from collections.abc import Mapping
from datetime import date
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.diagnostics import SolverDiagnostic


class MaxShiftsPerWeek:
    """Ensure no employee is assigned more than 5 shifts in any calendar week."""

    id: ClassVar[str] = "max_shifts_per_week"
    required: ClassVar[bool] = True

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]:
        del params  # Unused if constraint has no dynamic parameters

        max_shifts = 5

        # Group assignment variables by (employee_id, calendar_week)
        vars_by_employee_week: defaultdict[tuple[int, int], list[cp_model.IntVar]] = defaultdict(list)

        for (employee_id, _unit, assignment_date, _shift, _role), var in ctx.assignment_variables.items():
            calendar_week = assignment_date.isocalendar().week
            vars_by_employee_week[(employee_id, calendar_week)].append(var)

        # Post the linear constraint to the CP-SAT model
        for (employee_id, week), vars_in_week in vars_by_employee_week.items():
            ctx.model.add(sum(vars_in_week) <= max_shifts).with_name(
                f"max_shifts_emp{employee_id}_wk{week}"
            )

        return ()

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        del params
        max_shifts = 5
        findings: list[AuditFinding] = []

        # Count actual assignments in the solved roster by employee and week
        counts_by_employee_week: defaultdict[tuple[int, int], int] = defaultdict(int)
        for assignment in ctx.assignments:
            week = assignment.date.isocalendar().week
            counts_by_employee_week[(assignment.employee_id, week)] += 1

        for (employee_id, week), count in counts_by_employee_week.items():
            if count > max_shifts:
                findings.append(
                    AuditFinding(
                        code="max_shifts_per_week.exceeded",
                        severity=AuditSeverity.ERROR,
                        source_id=self.id,
                        message=(
                            f"Employee exceeded maximum allowed shifts in week {week}: "
                            f"employee_id={employee_id}, assigned={count}, max={max_shifts}."
                        ),
                    )
                )

        return tuple(findings)
```

---

## Step 2: Key Context Objects

When writing constraints, you interact with two context objects:

### `SolverContext` (During Model Building)
* `ctx.model`: The OR-Tools `cp_model.CpModel` instance.
* `ctx.assignment_variables`: Mapping of `AssignmentVariableKey` tuple `(employee_id, planning_unit_id, date, shift_id, staff_level)` to CP-SAT Boolean variables.
* `ctx.dataset`: The canonical [`SchedulingDataset`](https://github.com/CombiRWTH/StaffScheduling/blob/main/src/scheduling/domain/dataset.py) containing employees, shifts, demands, and calendar bounds.
* `ctx.index`: Precomputed lookup indices (e.g. `ctx.index.shifts_by_id`, `ctx.index.dates`).

### `AuditContext` (Post-Solve Auditing)
* `ctx.solution`: The solved schedule containing actual `assignments`.
* `ctx.dataset`: The original input dataset.

---

## Step 3: Register the Constraint in the Builder

Open [`src/scheduling/solver/cp_sat/builder.py`](https://github.com/CombiRWTH/StaffScheduling/blob/main/src/scheduling/solver/cp_sat/builder.py) and add your constraint to `CP_SAT_CONSTRAINTS`:

```python
from scheduling.solver.cp_sat.constraints.max_shifts_per_week import MaxShiftsPerWeek

CP_SAT_CONSTRAINTS: tuple[Constraint, ...] = (
    MinimumStaffing(),
    FreeDayAfterNightShiftPhase(),
    RoundsInEarlyShift(),
    AvailabilitiesConstraint(),
    HierarchyOfIntermediateShifts(),
    OneAssignmentPerDay(),
    TargetWorkingTime(),
    MaxShiftsPerWeek(),  # <-- Register new constraint here
)
```

---

## Step 4: Write Unit Tests

Add unit tests under `tests/cp/constraints/` to verify constraint formulation and audit reporting using `create_context` or `AuditContext`:

```python
from scheduling.solver.cp_sat.context import AuditContext, create_context
from scheduling.solver.cp_sat.variables import create_assignment_variables
from scheduling.solver.index import build_schedule_index


def test_max_shifts_per_week_add_to_model(sample_dataset):
    ctx = create_context(dataset=sample_dataset)
    create_assignment_variables(ctx)

    diagnostics = MaxShiftsPerWeek().add_to_model(ctx, params={})
    assert diagnostics == ()


def test_max_shifts_per_week_audit_clean(sample_dataset, valid_assignments):
    ctx = AuditContext(
        dataset=sample_dataset,
        index=build_schedule_index(sample_dataset),
        assignments=valid_assignments,
    )
    findings = MaxShiftsPerWeek().audit(ctx, params={})
    assert len(findings) == 0
```
