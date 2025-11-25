import pandas as pd
from .utils import convert_solution_to_shiftsets


def hamming_distance_matrix(solutions):
    shift_solutions = [
        convert_solution_to_shiftsets(sol.variables) for sol in solutions
    ]
    n = len(shift_solutions)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            all_shifts = set(shift_solutions[i].keys()) | set(shift_solutions[j].keys())
            diff = 0
            for shift in all_shifts:
                empA = shift_solutions[i].get(shift, set())
                empB = shift_solutions[j].get(shift, set())
                if empA != empB:
                    diff += 1
            matrix[i][j] = diff
    return pd.DataFrame(
        matrix,
        columns=[f"Sol {i}" for i in range(n)],
        index=[f"Sol {i}" for i in range(n)],
    )


def print_hamming_table(solutions):
    df = hamming_distance_matrix(solutions)
    print(df)
