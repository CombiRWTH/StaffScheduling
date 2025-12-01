import pandas as pd
from scipy.optimize import linear_sum_assignment
from .utils import convert_solution_to_shiftsets

# .\.venv\Scripts\python.exe -m ensurepip --upgrade
# Get-ChildItem .\.venv\Scripts\pip*
# .\.venv\Scripts\python.exe -m pip install scipy
# .\.venv\Scripts\python.exe -c "import scipy; print(scipy.__version__)"


def hungarian_distance(solA, solB):
    shiftsA = convert_solution_to_shiftsets(solA.variables)
    shiftsB = convert_solution_to_shiftsets(solB.variables)

    employeesA = list(set(emp for emps in shiftsA.values() for emp in emps))
    employeesB = list(set(emp for emps in shiftsB.values() for emp in emps))

    n = max(len(employeesA), len(employeesB))
    employeesA += [None] * (n - len(employeesA))
    employeesB += [None] * (n - len(employeesB))

    # Kostenmatrix: 0, A und B äquivalent; 1 sonst
    cost_matrix = [[0] * n for _ in range(n)]
    for i, a in enumerate(employeesA):
        for j, b in enumerate(employeesB):
            if a is None or b is None:
                cost_matrix[i][j] = 1
                continue
            # Menge der Schichten, die von a in Plan A abgedeckt werden
            shifts_a = {s for s, emps in shiftsA.items() if a in emps}
            # Menge der Schichten, die von b in Plan B abgedeckt werden
            shifts_b = {s for s, emps in shiftsB.items() if b in emps}
            # Kosten = 1, wenn die Abdeckungen unterschiedlich sind, 0 wenn identisch
            cost_matrix[i][j] = 0 if shifts_a == shifts_b else 1

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    return sum(cost_matrix[i][j] for i, j in zip(row_ind, col_ind))


def hungarian_distance_matrix(solutions):
    n = len(solutions)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            matrix[i][j] = hungarian_distance(solutions[i], solutions[j])
    return pd.DataFrame(
        matrix,
        columns=[f"Sol {i}" for i in range(n)],
        index=[f"Sol {i}" for i in range(n)],
    )


def print_hungarian_table(solutions):
    df = hungarian_distance_matrix(solutions)
    print(df)
