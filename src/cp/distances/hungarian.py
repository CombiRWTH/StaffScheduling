import pandas as pd
from scipy.optimize import linear_sum_assignment
from .utils import convert_solution_to_shiftsets
from pathlib import Path

# .\.venv\Scripts\python.exe -m ensurepip --upgrade
# Get-ChildItem .\.venv\Scripts\pip*
# .\.venv\Scripts\python.exe -m pip install scipy
# .\.venv\Scripts\python.exe -c "import scipy; print(scipy.__version__)"


def _get_solution_files():
    base_path = Path(__file__).resolve().parents[3] / "found_solutions"
    if not base_path.exists():
        raise FileNotFoundError(f"Folder not found: {base_path}")

    json_files = sorted(base_path.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {base_path}")

    return json_files


def hungarian_distance(json_file_A, json_file_B):
    shiftsA = convert_solution_to_shiftsets(json_file_A)
    shiftsB = convert_solution_to_shiftsets(json_file_B)

    employeesA = list({emp for emps in shiftsA.values() for emp in emps})
    employeesB = list({emp for emps in shiftsB.values() for emp in emps})

    n = max(len(employeesA), len(employeesB))
    employeesA += [None] * (n - len(employeesA))
    employeesB += [None] * (n - len(employeesB))

    cost_matrix = [[0] * n for _ in range(n)]

    for i, a in enumerate(employeesA):
        for j, b in enumerate(employeesB):
            if a is None or b is None:
                cost_matrix[i][j] = 1
                continue

            shifts_a = {s for s, emps in shiftsA.items() if a in emps}
            shifts_b = {s for s, emps in shiftsB.items() if b in emps}

            cost_matrix[i][j] = 0 if shifts_a == shifts_b else 1

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    return sum(cost_matrix[i][j] for i, j in zip(row_ind, col_ind))


def hungarian_distance_matrix():
    json_files = _get_solution_files()
    n = len(json_files)

    matrix = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            matrix[i][j] = hungarian_distance(json_files[i], json_files[j])

    return pd.DataFrame(
        matrix,
        columns=[f"Sol {i}" for i in range(n)],
        index=[f"Sol {i}" for i in range(n)],
    )


def print_hungarian_table():
    df = hungarian_distance_matrix()
    print(df)
