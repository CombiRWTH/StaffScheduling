import networkx as nx
from .utils import convert_solution_to_shiftsets


def build_shift_graph(solution):
    shift_sets = convert_solution_to_shiftsets(solution.variables)
    G = nx.Graph()

    for shift, employees in shift_sets.items():
        shift_node = f"SHIFT_{shift}"
        G.add_node(shift_node, bipartite=1)

        for emp in employees:
            emp_node = f"EMP_{emp}"
            G.add_node(emp_node, bipartite=0)
            G.add_edge(emp_node, shift_node)

    return G


def graph_isomorphic(solutions):
    graphs = [build_shift_graph(sol) for sol in solutions]
    n = len(graphs)

    iso_matrix = [[False] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            matcher = nx.isomorphism.GraphMatcher(graphs[i], graphs[j])
            iso_matrix[i][j] = matcher.is_isomorphic()

    return iso_matrix


def print_iso_matrix(solutions):
    matrix = graph_isomorphic(solutions)
    for row in matrix:
        print(row)
