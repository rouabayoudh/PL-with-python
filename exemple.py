from gurobipy import Model, GRB

# Créer un nouveau modèle
model = Model("Extended LP")

# Ajouter des variables (avec des bornes personnalisées)
x = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="x")  # x >= 0
y = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="y")  # y >= 0
w = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="w")  # w >= 0 (variable auxiliaire)

# Définir des paramètres personnalisés (optionnel)
model.setParam("OutputFlag", 1)  # Affiche les logs (1 pour activé, 0 pour désactivé)
model.setParam("TimeLimit", 10)  # Limite de temps d'exécution à 10 secondes

# Ajouter une fonction objectif étendue : Max z = 3x + 2y - 2w
model.setObjective(3 * x + 2 * y - 2 * w, GRB.MAXIMIZE)

# Ajouter des contraintes
model.addConstr(x + 2 * y + w <= 4, "Constraint1")  # x + 2y + w ≤ 4
model.addConstr(x + y <= 2, "Constraint2")          # x + y ≤ 2
model.addConstr(y - w >= 0, "Constraint3")          # y - w ≥ 0

# Optimiser le modèle
model.optimize()

# Afficher les résultats
if model.status == GRB.OPTIMAL:
    print("Solution optimale trouvée :")
    for var in model.getVars():
        print(f"{var.varName} = {var.x}")  # Affiche les valeurs des variables
    print(f"Valeur optimale de l'objectif (z) = {model.objVal}")
else:
    print("Aucune solution optimale trouvée.")

