import itertools
import subprocess
from argparse import ArgumentParser
from typing import Any


class Graph:
    vertices: dict[int, set[int]] = {}

    def add_vertex_with_edges(self, vertex: int, edges: set[int]) -> None:
        self.vertices[vertex] = edges

# Variable x_iv means vertex `v` is at position `i` in the clique
def var(i: int, v: int) -> int:
    return i * num_vertices + v + 1


def convert_problem_instance_to_cnf(graph: Graph, k: int) -> tuple[list, int]:
    """
    - Each pair of the vertices in the clique is connected by an edge
    - At most one vertex occupies each position in the clique
    :param graph: Graph instance of the problem
    :param k: Exactly k vertices are in the clique

    """
    global num_vertices
    num_vertices = len(graph.vertices.keys())
    vertices = list(graph.vertices.keys())
    cnf = []

    # 1) There is i-th vertex in the clique
    for i in range(1, k+1):
        cnf.append([var(i, v) for v in vertices])


    # 2) The i-th and j-th vertices are not same
    for i, j in itertools.combinations(range(1, k+1), 2):
        for v in vertices:
            cnf.append([-var(i, v), -var(j, v)])

    # 3) Any two vertex in the clique is connected
    for i, j in itertools.combinations(range(1, k+1), 2):
        for v in vertices:
            for u in vertices:
                if u != v and u not in graph.vertices[v]:
                    cnf.append([-var(i, v), -var(j, u)])

    return cnf, max(max(sublist) for sublist in cnf)

def load_problem_instance(file_name: str) -> Graph:
    graph = Graph()

    with open(file_name, "r") as file:
        for line in file:
            vertex, edges_str = line.split(':')
            graph.add_vertex_with_edges(int(vertex), {int(edge) for edge in edges_str.split(',')})

    return graph

def print_result(result: Any, graph: Graph, k: int) -> None:
    for line in result.stdout.decode('utf-8').split('\n'):
        print(line)  # print the whole output of the SAT solver to stdout, so you can see the raw output for yourself

    # parse the model from the output of the solver
    # the model starts with 'v'
    model = []
    for line in result.stdout.decode('utf-8').split('\n'):
        if line.startswith("v"):    # there might be more lines of the model, each starting with 'v'
            vars = line.split(" ")
            vars.remove("v")
            model.extend(int(v) for v in vars)
    model.remove(0) # 0 is the end of the model, just ignore it

    clique = []
    vertices = list(graph.vertices.keys())

    for i in range(1, k+1):
        for v in vertices:
            try:
                if model[var(i, v)] > 0:
                    clique.append(v)
            except IndexError:
                pass

    print(f"Maximum clique size: {k}, {clique}")


def call_solver(instance: Graph, output_name: str, solver_name: str, verbosity: int) -> tuple[Any, int]:
    k = len(instance.vertices.keys())
    while True:
        if k == 0:
            raise IndexError("TF")
        cnf, nr_vars = convert_problem_instance_to_cnf(instance, k)
        # print CNF into formula.cnf in DIMACS format
        with open(output_name, "w") as file:
            file.write("p cnf " + str(nr_vars) + " " + str(len(cnf)) + '\n')
            for clause in cnf:
                file.write(' '.join(str(lit) for lit in clause) + ' 0\n')

        result = subprocess.run(['./' + solver_name, '-model', '-verb=' + str(verbosity) , output_name], stdout=subprocess.PIPE)

        if result.returncode == 10:  # returncode for SAT is 10, for UNSAT is 20
            return result, k
        k -= 1


if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        default="instances/graph_1.in",
        type=str,
        help=(
            "The instance file."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="formula.cnf",
        type=str,
        help=(
            "Output file for the DIMACS format (i.e. the CNF formula)."
        ),
    )
    parser.add_argument(
        "-v",
        "--verb",
        default=1,
        type=int,
        choices=range(0,2),
        help=(
            "Verbosity of the SAT solver used."
        ),
    )
    args = parser.parse_args()

    # get the input instance
    instance = load_problem_instance(args.input)

    # call the SAT solver and get the result
    result, clique_size = call_solver(instance, args.output, "glucose-syrup", args.verb)
    # interpret the result and print it in a human-readable format
    print_result(result, instance, clique_size)
