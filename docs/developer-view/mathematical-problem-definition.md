# Mathematical Problem Definition

This page gives a formal description of the staff scheduling problem as a **Constraint Programming / Integer Linear Programming** model. It complements the higher-level [Problem Definition](../user-view/problem-definition.md) and the [OR-Tools & CP-SAT](./ortools.md) implementation guide.

---

## Index Notation

| Symbol | Description |
|---|---|
| $E$ | Set of employees |
| $U$ | Set of planning units (wards/stations) |
| $D$ | Set of calendar dates in the planning month |
| $S$ | Set of shifts (Early, Late, Night, Intermediate, …) |
| $L$ | Set of staff qualification levels (`PROFESSIONAL`, `ASSISTANT`, `TRAINEE`) |
| $\text{Eligible}(e, u, d, s, l)$ | Boolean: employee $e$ is eligible for unit $u$, date $d$, shift $s$, role $l$ |

---

## Decision Variables

For every eligible assignment slot, a Boolean variable is introduced:

$$x_{e,u,d,s,l} \in \{0, 1\} \quad \forall (e, u, d, s, l) \in \text{Eligible}$$

$x_{e,u,d,s,l} = 1$ means employee $e$ is assigned to planning unit $u$ on date $d$, working shift $s$ in role $l$.

Ineligible slots have no variable — this prunes the search space significantly before the solver starts.

---

## Hard Constraints

Hard constraints define the set of *feasible* schedules. Any schedule violating a hard constraint is rejected by CP-SAT as infeasible.

### Max One Shift Per Day

Each employee works at most one shift per calendar day:

$$\sum_{u \in U} \sum_{s \in S} \sum_{l \in L} x_{e,u,d,s,l} \leq 1 \quad \forall e \in E,\ d \in D$$

### Minimum Staffing

For each planning unit, date, shift, and qualification level, the required headcount must be met:

$$\sum_{e \in E} x_{e,u,d,s,l} \geq \text{demand}(u,d,s,l) \quad \forall (u,d,s,l)$$

where $\text{demand}(u,d,s,l) > 0$ comes from the `DemandRequirement` records.

### Availability (Vacations, Absences, External Shifts)

Employees with a hard unavailability on date $d$ must not be assigned:

$$\sum_{u,s,l} x_{e,u,d,s,l} = 0 \quad \forall e \in E,\ d \in \text{Unavailable}(e)$$

For employees pinned to specific shifts only (`AVAILABLE_ONLY`), all other shift variables are forced to zero.

### Target Working Hours

Each employee's total planned working minutes must fall within a contracted range:

$$T^{\min}_e \leq \sum_{u,d,s,l} \text{duration}(s) \cdot x_{e,u,d,s,l} \leq T^{\max}_e \quad \forall e \in E$$

where $T^{\min}_e$ and $T^{\max}_e$ allow a deviation of at most one full shift (≈7.67 hours = 460 minutes) from the monthly target.

### Free Day After Night Shift Phase

If employee $e$ works a night shift on date $d$ and does **not** work a night shift on date $d+1$ (end of a night block), then $d+1$ must be a rest day:

$$\text{NightPhaseEnd}(e, d) \Rightarrow \sum_{u,s,l} x_{e,u,d+1,s,l} = 0$$

### Ward Rounds (Visiten)

On every weekday, at least one employee with the `ROUNDS` capability must be assigned to an early shift:

$$\sum_{e \in \text{Capable}(\text{ROUNDS})} x_{e,u,d,F,l} \geq 1 \quad \forall u,\ d \in \text{Weekdays}$$

where $F$ denotes the Early shift.

### Hierarchy of Intermediate Shifts

Intermediate shifts (`Z`) are only assigned after minimum staffing is satisfied. The solver enforces a priority order: one weekday intermediate shift per day before weekend intermediates, then two weekday intermediates, then two weekend intermediates.

---

## Soft Objectives

Soft objectives define *preferences* that are not strictly required but should be maximized where possible. They are modelled as **penalty expressions** minimized by the solver:

$$\min \sum_{i} w_i \cdot P_i$$

where $w_i$ is the user-configured weight for objective $i$, and $P_i$ is the total penalty incurred.

| Objective | Penalty expression $P_i$ |
|---|---|
| **Wishes** | Count of unfulfilled `FREE_DAY`, `FREE_SHIFT`, `PREFERRED_DAY`, `PREFERRED_SHIFT` wishes |
| **Overtime** | $\sum_e \max(0,\ \text{worked}_e - T^{\text{target}}_e) + \max(0,\ T^{\text{target}}_e - \text{worked}_e)$ |
| **Consecutive night shifts** | Excess length of night-shift streaks beyond a minimum block |
| **Free day after night phase** | Counts missing second rest day after a night shift block (soft complement to the hard constraint) |
| **Every second weekend free** | Penalizes every weekend (Sat+Sun) that is not free when the previous one was also worked |
| **Free days near weekend** | Penalizes missing rest days on Fri, Sat, Sun, Mon |
| **Forward shift rotation** | Penalizes backward shifts (Late → Early, Night → Late, etc.) in sequence |
| **Preferred block length** | Penalizes shift blocks shorter or longer than the preferred ergonomic block length |
| **Consecutive working days** | Penalizes streaks of 6 or more consecutive working days |
| **Balance generated assignments** | Minimizes the maximum generated-shift load on any one employee |

---

## Solution Quality

The solver reports one of the following statuses:

| Status | Meaning |
|---|---|
| `OPTIMAL` | Proven minimum penalty found within the time limit |
| `FEASIBLE` | A valid schedule was found; better solutions may exist (time limit reached) |
| `INFEASIBLE` | No schedule satisfying all hard constraints exists |
| `UNKNOWN` | Time limit reached before any feasible solution was found |

After solving, the `AuditReport` independently re-verifies the solution against all hard constraints to produce a list of `AuditFinding` records.
