# Extending the Solver (How-To Guides)

This section provides step-by-step developer guides for extending the **Google OR-Tools CP-SAT** optimization engine with new business rules, goals, and decision variables.

---

## The Three Extensible Components

The solver architecture is organized around three primary concepts:

### 1. [Adding Variables](./how-to-add-variable.md)
* **Decision Variables:** Represent choices the solver makes (e.g. `x[e, u, d, s, l] ∈ {0, 1}`).
* **Intermediate / Helper Variables:** Defined inside constraints or objectives to model complex non-linear expressions (e.g., whether an employee worked on a given day, cumulative overtime minutes, or consecutive shift streak lengths).

### 2. [Adding Constraints](./how-to-add-constraint.md)
* **Hard Feasibility Rules:** Rules that **must** be satisfied in every generated schedule (e.g. maximum 1 shift per day, mandatory 11-hour rest time, minimum required staffing, monthly contracted hours).
* Any schedule violating a hard constraint is rejected by CP-SAT as **infeasible**.
* Conforms to the [`Constraint`](file:///c:/Users/jonas/Dev/StaffScheduling/src/scheduling/solver/cp_sat/constraint.py) protocol.

### 3. [Adding Objectives](./how-to-add-objective.md)
* **Soft Optimization Goals:** Preferences and ergonomic guidelines that **should** be maximized or minimized (e.g. employee shift wishes, alternating weekends off, minimizing consecutive nights, clockwise shift rotation).
* Evaluated into integer `Penalty` expressions and multiplied by user-configured weights from `/weights`.
* Conforms to the [`Objective`](file:///c:/Users/jonas/Dev/StaffScheduling/src/scheduling/solver/cp_sat/objective.py) protocol.

---

## When to Use Which Component?

| Requirement | Use a Constraint | Use an Objective |
|---|:---:|:---:|
| Legal labor regulations (e.g. 11h rest period, max working hours) | ✅ | ❌ |
| Hospital ward safety minimums (e.g. 2 professionals in early shift) | ✅ | ❌ |
| Hard contracts (e.g. approved vacation days, employee cannot work nights) | ✅ | ❌ |
| Individual nurse shift preferences and requested off-days | ❌ | ✅ |
| Ergonomic shift patterns (e.g. avoiding 6 nights in a row, forward rotation) | ❌ | ✅ |
| Fairness and equitable distribution of unpopular shifts | ❌ | ✅ |

For an overview of the solver model builder and execution lifecycle, see the [Codebase Overview](../codebase-overview.md) and [Google OR-Tools and CP-SAT Solver](../ortools.md).
