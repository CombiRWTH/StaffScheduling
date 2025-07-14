# Overview
This section presents the formal mathematical formulation of the shift scheduling problem as a constraint satisfaction and optimization model. The scheduling problem is modeled as an Integer Programming (IP) problem, where binary decision variables represent shift assignments and various constraints ensure operational feasibility, legal compliance, and employee satisfaction. Each constraint is expressed using mathematical notation. The formulation includes hard constraints that must be satisfied for a valid solution, as well as soft constraints implemented as penalty terms in the objective function.

# Sets and Indices

- $\mathcal{E}$: Set of all employees
  - $\mathcal{E}_F \subseteq \mathcal{E}$: Subset of qualified staff (Fachkräfte)
  - $\mathcal{E}_H \subseteq \mathcal{E}$: Subset of auxiliary staff (Hilfskräfte)
  - $\mathcal{E}_A \subseteq \mathcal{E}$: Subset of trainees (Azubis)
- $\mathcal{D}$: Set of days in the planning horizon (typically one month)
- $\mathcal{S}$: Set of shifts $\{F, Z, S, N, ...\}$
  - $F$: Early shift (Früh)
  - $Z$: Intermediate shift (Zwischen)
  - $S$: Late shift (Spät)
  - $N$: Night shift (Nacht)

# Parameters

- $\text{duration}_s$: Duration of shift $s$ in minutes
- $R^F_{d,s}$: Minimum required qualified staff for day $d$, shift $s$
- $R^H_{d,s}$: Minimum required auxiliary staff for day $d$, shift $s$
- $R^A_{d,s}$: Minimum required trainees for day $d$, shift $s$
- $\text{target}_e$: Target working minutes for employee $e$
- $\text{start}_{d,s}$: Start time of shift $s$ on day $d$ (in minutes from midnight)
- $\text{end}_{d,s}$: End time of shift $s$ on day $d$ (in minutes from midnight)

# Decision Variables

## Primary Variables
- $x_{e,d,s} \in \{0,1\}$: Binary variable equal to 1 if employee $e$ is assigned to shift $s$ on day $d$, 0 otherwise

## Auxiliary Variables
- $h_e$: Total minutes worked by employee $e$ in the planning period
- $y_{e,d} \in \{0,1\}$: Binary variable equal to 1 if employee $e$ works on day $d$

# Objective Function

Minimize weighted sum of penalties:

$$\min \sum_{i} w_i \cdot P_i$$

Where $P_i$ represents different penalty terms (overtime, consecutive shifts, etc.) and $w_i$ are their respective weights.

# Constraints

## 1. Minimum Staffing Requirements
For each day $d$ and shift $s$:

$$\sum_{e \in \mathcal{E}_F} x_{e,d,s} \geq R^F_{d,s} \quad \forall d \in \mathcal{D}, s \in \mathcal{S}$$

$$\sum_{e \in \mathcal{E}_H} x_{e,d,s} \geq R^H_{d,s} \quad \forall d \in \mathcal{D}, s \in \mathcal{S}$$

$$\sum_{e \in \mathcal{E}_A} x_{e,d,s} \geq R^A_{d,s} \quad \forall d \in \mathcal{D}, s \in \mathcal{S}$$

## 2. One Shift per Day
Each employee can work at most one shift per day:

$$\sum_{s \in \mathcal{S}} x_{e,d,s} \leq 1 \quad \forall e \in \mathcal{E}, \forall d \in \mathcal{D}$$

## 3. Working Time Calculation
Total working time for each employee:

$$h_e = \sum_{d \in \mathcal{D}} \sum_{s \in \mathcal{S}} x_{e,d,s} \cdot \text{duration}_s \quad \forall e \in \mathcal{E}$$

## 4. Target Working Time Constraint
Working time should be within tolerance of target:

$$|h_e - \text{target}_e| \leq 460 \quad \forall e \in \mathcal{E}$$

Or equivalently:

$$\text{target}_e - 460 \leq h_e \leq \text{target}_e + 460 \quad \forall e \in \mathcal{E}$$

## 5. Vacation and Leave Days
If employee $e$ is on leave on day $d$:

$$\sum_{s \in \mathcal{S}} x_{e,d,s} = 0 \quad \forall e \in \mathcal{E}, \forall d \in \text{VacationDays}_e$$

## 6. Minimum Rest Time Between Shifts
At least 11 hours (660 minutes) rest between consecutive shifts:

$$x_{e,d_1,s_1} = 1 \land x_{e,d_2,s_2} = 1 \land d_2 = d_1 + 1 \Rightarrow \text{start}_{d_2,s_2} - \text{end}_{d_1,s_1} \geq 660$$

## 7. Free Day After Night Shift Phase
No night shift before a free day:

$$\sum_{s \in \mathcal{S}} x_{e,d,s} = 0 \Rightarrow x_{e,d-1,N} = 0$$

## 8. Planned Shifts (Fixed Assignments)
For predetermined shift assignments:

$$x_{e,d,s} = 1 \quad \forall (e,d,s) \in \text{PlannedShifts}$$

## 9. Forbidden Shifts
Certain employees cannot work specific shifts:

$$x_{e,d,s} = 0 \quad \forall (e,d,s) \in \text{ForbiddenShifts}$$

## 10. Maximum Consecutive Working Days
Limit consecutive working days (typically 5):

$$\sum_{i=0}^{5} y_{e,d+i} \leq 5 \quad \forall e \in \mathcal{E}, \forall d \in \mathcal{D}$$

Where:

$$y_{e,d} \geq \sum_{s \in \mathcal{S}} x_{e,d,s}$$

# Special Employee Constraints Examples

## Management Constraints (e.g., Branz)
- Fixed management shifts: $x_{\text{Branz},\text{Tuesday},Z60} = 1$, $x_{\text{Branz},\text{Thursday},Z60} = 1$
- No night shifts: $x_{\text{Branz},d,N} = 0 \quad \forall d \in \mathcal{D}$

## Night Shift Only Employees
For employees restricted to night shifts:

$$x_{e,d,s} = 0 \quad \forall s \neq N, \forall d \in \mathcal{D}, \forall e \in \text{NightOnlyEmployees}$$

## No Night Shift Employees
For employees who cannot work nights:

$$x_{e,d,N} = 0 \quad \forall d \in \mathcal{D}, \forall e \in \text{NoNightEmployees}$$
