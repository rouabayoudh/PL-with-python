from flask import Flask, render_template, request, redirect, url_for
from gurobipy import Model, GRB, quicksum

app = Flask(__name__)


def solve_graph_coloring(num_vertices, edges):
    
    """Solve the graph coloring problem using Gurobi."""
    # Create the model
    model = Model("Graph Coloring")

    # Create variables
    # x[v, c] = 1 if vertex v is assigned color c
    max_colors = num_vertices  # Worst-case: all vertices need different colors
    x = model.addVars(num_vertices, max_colors, vtype=GRB.BINARY, name="x")

    # Objective: Minimize the number of colors used
    y = model.addVars(max_colors, vtype=GRB.BINARY, name="y")  # y[c] = 1 if color c is used
    model.setObjective(quicksum(y[c] for c in range(max_colors)), GRB.MINIMIZE)

    # Constraints
    # Each vertex must be assigned exactly one color
    for v in range(num_vertices):
        model.addConstr(quicksum(x[v, c] for c in range(max_colors)) == 1)

    # Adjacent vertices must not share the same color
    for u, v in edges:
        for c in range(max_colors):
            model.addConstr(x[u, c] + x[v, c] <= y[c])

    # Solve the model
    model.optimize()


    # Extract the solution
    solution = {}
    for v in range(num_vertices):
        for c in range(max_colors):
            if x[v, c].x > 0.5:
                solution[v] = c
                break

    num_colors = sum(y[c].x > 0.5 for c in range(max_colors))
    print(solution, int(num_colors))
    return solution, int(num_colors)



if __name__ == "__main__":
    app.run(debug=True)
