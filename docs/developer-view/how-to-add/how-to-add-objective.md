# How to Add a New Objective

This guide explains how to create and register a new **soft optimization objective** in the CP-SAT solver.

---

## Overview

Unlike hard constraints (which must be 100% satisfied), **objectives represent preferences, ergonomic recommendations, or fairness goals**.

Objectives do not make a schedule infeasible. Instead, they define **penalties** for undesirable patterns (e.g. working weekends, backward shift rotations, or unfulfilled wishes). The solver minimizes the weighted sum of all penalties:

$$\text{minimize} \sum_i w_i \cdot P_i$$

Where $w_i$ is the user-configured weight multiplier, and $P_i$ is the penalty expression.

Every objective must conform to the **[`Objective`](file:///c:/Users/jonas/Dev/StaffScheduling/src/scheduling/solver/cp_sat/objective.py)** protocol:

```python
class Objective(Protocol):
    id: ClassVar[str]

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]: ...

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]: ...
```

---

## The `Penalty` Dataclass

When implementing `add_to_model`, your objective returns a tuple of **`Penalty`** instances:

```python
@dataclass(frozen=True, slots=True)
class Penalty:
    objective_id: str             # Matches self.id
    name: str                     # Descriptive name (e.g. "weekend_shift_penalty")
    expression: cp_model.LinearExpr  # IntVar, BoolVar, or linear sum to minimize
    multiplier: int = 1           # Internal scaling multiplier
```

!!! important "Weight Separation"
    Objectives **never** apply the global user weight directly. The model builder in [`builder.py`](file:///c:/Users/jonas/Dev/StaffScheduling/src/scheduling/solver/cp_sat/builder.py) retrieves user weights centrally from `ctx.dataset.objective_weights` and multiplies them automatically.

---

## Step 1: Create the Objective Class

Create a new file under [`src/scheduling/solver/cp_sat/objectives/`](file:///c:/Users/jonas/Dev/StaffScheduling/src/scheduling/solver/cp_sat/objectives/), for example `minimize_weekend_shifts.py`:

```python
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class MinimizeWeekendShifts:
    """Penalize assigning employees to shifts on Saturdays and Sundays."""

    id: ClassVar[str] = "minimize_weekend_shifts"

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        del params

        weekend_vars: list[cp_model.IntVar] = []

        # Find all assignment variables scheduled on Saturdays (weekday 5) or Sundays (weekday 6)
        for (_emp_id, _unit_id, assignment_date, _shift_id, _role), var in ctx.assignment_variables.items():
            if assignment_date.weekday() in (5, 6):
                weekend_vars.append(var)

        if not weekend_vars:
            return ()

        # Sum of all weekend shifts worked
        total_weekend_shifts = sum(weekend_vars)

        return (
            Penalty(
                objective_id=self.id,
                name="total_weekend_shifts",
                expression=total_weekend_shifts,
                multiplier=1,
            ),
        )

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        del params

        # Count weekend shifts in the generated roster
        total_weekend_assignments = sum(
            1 for a in ctx.solution.assignments if a.date.weekday() in (5, 6)
        )

        return (
            AuditFinding(
                code="weekend_shifts.count",
                severity=AuditSeverity.INFO,
                source_id=self.id,
                message=f"Total weekend shifts scheduled: {total_weekend_assignments}.",
            ),
        )
```

---

## Step 2: Register the Objective in the Builder

Add your objective to `CP_SAT_OBJECTIVES` in [`src/scheduling/solver/cp_sat/builder.py`](file:///c:/Users/jonas/Dev/StaffScheduling/src/scheduling/solver/cp_sat/builder.py):

```python
from scheduling.solver.cp_sat.objectives.minimize_weekend_shifts import MinimizeWeekendShifts

CP_SAT_OBJECTIVES: tuple[Objective, ...] = (
    TemporaryBalanceGeneratedAssignments(),
    MinimizeOvertime(),
    NotTooManyConsecutiveDays(),
    PreferredBlockLength(),
    RotateShiftsForward(),
    EverySecondWeekendFree(),
    FairPreferencesObjective(),
    FreeDaysAfterNightShiftPhase(),
    MinimizeConsecutiveNightShifts(),
    FreeDaysNearWeekend(),
    MinimizeWeekendShifts(),  # <-- Register new objective here
)
```

---

## Step 3: Configure Weights

To control how heavily CP-SAT penalizes this objective relative to other goals:

1. **Via the Web Interface (StaffSchedulingWeb):** Adjust the weight slider under the **Weights** configuration page.
2. **Via the REST API:** Update the weight through `PUT /weights`.
3. **Via Offline JSON Cases:** Add the objective key to `cases/{case_id}/{MM_YYYY}/weights.json`:
   ```json
   {
       "minimize_weekend_shifts": 3,
       "wishes": 4,
       "overtime": 2
   }
   ```
