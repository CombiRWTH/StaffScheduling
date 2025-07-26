# Introduction

When faced with difficult scheduling, routing, or optimization problems, traditional programming methods often don't work well. These problems are known as combinatorial optimization problems. They can have millions or billions of possible solutions. This means that brute-force approaches are not a good way to solve them.

# What is SAT-Solving?

## The Boolean Satisfiability Problem

SAT (Boolean Satisfiability) is one of the most fundamental problems in computer science. At its core, SAT-solving asks a deceptively simple question: **Given a Boolean formula, is there an assignment of true/false values to its variables that makes the entire formula true?**

For example, consider this Boolean formula:
```
(A OR B) AND (NOT A OR C) AND (NOT B OR NOT C)
```

A SAT-solver would try to find values for A, B, and C that make this entire expression true. In this case, A=false, B=true, C=false would satisfy the formula.
# How SAT-Solving Works
## The Search Process

```
1. Make a decision (assign a variable)
2. Propagate consequences (what must follow?)
3. If conflict found:
   - Learn why the conflict occurred
   - Backtrack and try different path
4. If no conflict:
   - Continue with next decision
5. Repeat until solution found or problem proven unsatisfiable
```

## Example: Simple Scheduling Problem

Consider scheduling 3 employees (A, B, C) to 2 shifts (Morning, Evening) where:
- Each shift needs exactly 1 person
- Employee A cannot work Evening shift

Variables:
- `A_Morning`, `A_Evening`, `B_Morning`, `B_Evening`, `C_Morning`, `C_Evening`

Constraints:
```
// Each shift needs exactly one person
A_Morning + B_Morning + C_Morning = 1
A_Evening + B_Evening + C_Evening = 1

// Employee A cannot work evening
NOT A_Evening

// Each person works at most one shift
A_Morning + A_Evening ≤ 1
B_Morning + B_Evening ≤ 1
C_Morning + C_Evening ≤ 1
```

A SAT-solver would systematically explore assignments until finding a valid solution.

# Google's OR-Tools

## Basic Variables and Constraints

```python
from ortools.sat.python import cp_model

# Create model
model = cp_model.CpModel()

# Variables
x = model.new_int_var(0, 10, 'x')
y = model.new_int_var(0, 10, 'y')
z = model.new_bool_var('z')

# Constraints
model.add(x + y <= 15)
model.add(x >= 5).only_enforce_if(z)
model.add(x < 5).only_enforce_if(z.not())

# Objective
model.maximize(x + 2*y)
```

## Advanced Constraints

CP-SAT provides specialized constraints for common patterns:

```python
# All different constraint
model.add_all_different([x1, x2, x3, x4])

# Cumulative constraint (resource scheduling)
model.add_cumulative(starts, durations, demands, capacity)

# Table constraint (allowed combinations)
model.add_allowed_assignments([x, y, z],
    [(1, 2, 0), (2, 3, 1), (3, 1, 0)])

# Circuit constraint (routing problems)
model.add_circuit(nexts)
```

## Solving Process

```python
# Create solver
solver = cp_model.CpSolver()

# Optional: Set solving parameters
solver.parameters.max_time_in_seconds = 60.0
solver.parameters.num_search_workers = 8

# Solve
status = solver.solve(model)

# Check results
if status == cp_model.OPTIMAL:
    print(f'x = {solver.value(x)}')
    print(f'y = {solver.value(y)}')
    print(f'Objective = {solver.objective_value}')
```
