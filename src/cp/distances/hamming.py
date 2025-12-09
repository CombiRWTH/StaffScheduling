import pandas as pd
from .utils import convert_solution_to_shiftsets
from pathlib import Path


def hamming_distance_matrix():
    base_path = Path(__file__).resolve().parents[3] / "found_solutions"
    json_files = sorted(base_path.glob("*.json"))

    shift_solutions = [convert_solution_to_shiftsets(file) for file in json_files]
    n = len(shift_solutions)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            all_shifts = set(shift_solutions[i].keys()) | set(shift_solutions[j].keys())
            diff = 0
            for shift in all_shifts:
                empA = shift_solutions[i].get(shift, set())
                empB = shift_solutions[j].get(shift, set())

                diff += len(empA.symmetric_difference(empB))

            matrix[i][j] = diff

    return pd.DataFrame(
        matrix,
        columns=[f"Sol {i}" for i in range(n)],
        index=[f"Sol {i}" for i in range(n)],
    )


def print_hamming_table():
    df = hamming_distance_matrix()
    print(df)
