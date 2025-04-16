import traceback
from gurobipy import Model, GRB


def solve_blending_problem(ingredients, properties, property_bounds, total_quantity):
        try:
            # Validate inputs
            if not ingredients or not properties or not property_bounds:
                raise ValueError("Ingredients, properties, or property bounds are missing or empty.")
            if total_quantity <= 0:
                raise ValueError("Total quantity must be greater than zero.")
            for ingredient in ingredients:
                if not all(k in ingredient for k in ['name', 'cost_per_unit', 'available_quantity', 'properties']):
                    raise ValueError(f"Ingredient {ingredient} is missing required fields.")
            
            # Create Gurobi model
            model = Model("Blending Problem")
            model.setParam('OutputFlag', 0)  # Suppress solver output
            
            # Number of ingredients
            n = len(ingredients)

            # Decision variables: quantity of each ingredient
            x = model.addVars(n, lb=0, name="ingredient_quantity")

            # Objective: Minimize total cost
            model.setObjective(
                sum(x[i] * ingredients[i]['cost_per_unit'] for i in range(n)),
                GRB.MINIMIZE
            )

            # Constraint: Total quantity
            model.addConstr(
                sum(x[i] for i in range(n)) == total_quantity,
                "Total_Quantity"
            )

            # Constraints: Availability of ingredients
            for i in range(n):
                model.addConstr(
                    x[i] <= ingredients[i]['available_quantity'],
                    f"Availability_{i}"
                )

            # Constraints: Property bounds
            for prop_name in properties:
                prop_contribution = sum(
                    x[i] * ingredients[i]['properties'][prop_name] for i in range(n)
                )
                min_bound = property_bounds[prop_name]['min'] * total_quantity
                max_bound = property_bounds[prop_name]['max'] * total_quantity

                # Debug constraints
                print(f"Property: {prop_name}, Min Bound: {min_bound}, Max Bound: {max_bound}")

                model.addConstr(prop_contribution >= min_bound, f"{prop_name}_Min")
                model.addConstr(prop_contribution <= max_bound, f"{prop_name}_Max")

            # Solve the model
            model.optimize()

            # Check solution status
            if model.status == GRB.OPTIMAL:
                results = {
                    'status': 'Optimal Solution Found',
                    'total_cost': model.objVal,
                    'ingredient_quantities': {},
                    'property_totals': {}
                }

                for i in range(n):
                    results['ingredient_quantities'][ingredients[i]['name']] = x[i].x

                for prop_name in properties:
                    prop_total = sum(
                        x[i].x * ingredients[i]['properties'][prop_name] for i in range(n)
                    )
                    results['property_totals'][prop_name] = prop_total

                return results
            else:
                return {'status': 'No optimal solution found'}
        except Exception as e:
            return {
                'status': 'Error',
                'message': str(e),
                'traceback': traceback.format_exc()  # For debugging
            }