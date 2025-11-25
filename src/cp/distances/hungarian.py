import pandas as pd
from .utils import convert_solution_to_shiftsets


def hungarian_distance(solA, solB):
    shiftsA = convert_solution_to_shiftsets(solA.variables)
    shiftsB = convert_solution_to_shiftsets(solB.variables)

    all_shifts = list(set(shiftsA.keys()) | set(shiftsB.keys()))
    n = len(all_shifts)

    cost_matrix = [[0] * n for _ in range(n)]
    for i, shiftA in enumerate(all_shifts):
        empA = shiftsA.get(shiftA, set())
        for j, shiftB in enumerate(all_shifts):
            empB = shiftsB.get(shiftB, set())
            cost_matrix[i][j] = len(empA.symmetric_difference(empB))

    from copy import deepcopy

    cost = deepcopy(cost_matrix)
    u = [0] * n
    v = [0] * n
    p = [0] * n
    way = [0] * n

    for i in range(n):
        p[0] = i
        minv = [float("inf")] * n
        used = [False] * n
        j0 = 0
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = -1
            for j in range(n):
                if not used[j]:
                    cur = cost[i0][j] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    matching_cost = -v[0]
    return matching_cost


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
