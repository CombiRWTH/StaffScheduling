import networkx as nx
from pathlib import Path
from .utils import convert_solution_to_shiftsets


def build_shift_graph(solution_file):
    shift_sets = convert_solution_to_shiftsets(solution_file)
    G = nx.Graph()
    for shift, employees in shift_sets.items():
        shift_node = f"SHIFT_{shift}"
        G.add_node(shift_node, bipartite=1)
        for emp in employees:
            emp_node = f"EMP_{emp}"
            G.add_node(emp_node, bipartite=0)
            G.add_edge(emp_node, shift_node)
    return G


def graph_isomorphic():
    base_path = Path(__file__).resolve().parents[3] / "found_solutions"
    if not base_path.exists():
        raise FileNotFoundError(f"Folder not found: {base_path}")
    json_files = sorted(base_path.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in: {base_path}")

    graphs = [build_shift_graph(f) for f in json_files]
    n = len(graphs)
    iso_matrix = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            matcher = nx.isomorphism.GraphMatcher(graphs[i], graphs[j])
            iso_matrix[i][j] = matcher.is_isomorphic()
    return iso_matrix


def print_iso_matrix():
    matrix = graph_isomorphic()
    for row in matrix:
        print(row)
