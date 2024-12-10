def generate_complete_graph(file_name: str, n: int):
    with open(file_name, "w") as file:
        for i in range(1, n+1):
            file.write(f"{i}: {','.join([str(j)for j in range(1, n+1) if j != i])}\n")

generate_complete_graph("instances/graph_4.in", 100)