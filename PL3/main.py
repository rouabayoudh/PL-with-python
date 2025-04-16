import gurobipy as gp
from gurobipy import GRB

def solve_multi_product_inventory(periods, products, demands, holding_costs, ordering_costs, 
                                setup_costs, capacities, expiration_periods, shared_capacity=None, initial_inventory=None):
    """
    Solve a multi-period, multi-product inventory optimization problem with expiration dates.
    Inventory levels are calculated from order quantities and demands.

    Parameters:
    periods (int): Number of time periods
    products (int): Number of products
    demands (dict): Dictionary with (product, period) tuples as keys and demand values
    holding_costs (dict): Holding cost for each product
    ordering_costs (dict): Ordering cost per unit for each product
    setup_costs (dict): Fixed setup cost for ordering each product
    capacities (dict): Maximum inventory capacity for each product
    expiration_periods (dict): Number of periods each product can be stored before expiring
    shared_capacity (float): Optional shared warehouse capacity constraint
    initial_inventory (dict): Dictionary with product IDs as keys and initial inventory values
    """
    try:
        model = gp.Model("Multi_Product_Inventory_Optimization")
        
        # Decision Variables
        # Order quantities for each product in each period
        order = model.addVars([(p, t) for p in range(products) for t in range(periods)],
                            lb=0, vtype=GRB.CONTINUOUS, name="order")
        # Binary variable for setup costs
        y = model.addVars([(p, t) for p in range(products) for t in range(periods)],
                         vtype=GRB.BINARY, name="setup")
        # Variable tracking inventory age
        inv_age = model.addVars([(p, t, a) for p in range(products) 
                                for t in range(periods) 
                                for a in range(expiration_periods[p])],
                              lb=0, vtype=GRB.CONTINUOUS, name="inventory_age")
        
        # Objective Function: Minimize total costs (ordering, setup, and holding)
        obj = (gp.quicksum(ordering_costs[p] * order[p, t] + 
                          setup_costs[p] * y[p, t] +
                          holding_costs[p] * gp.quicksum(inv_age[p, t, a] 
                                                       for a in range(expiration_periods[p]))
                          for p in range(products) 
                          for t in range(periods)))
        model.setObjective(obj, GRB.MINIMIZE)
        
        # Constraints
        for p in range(products):
            shelf_life = expiration_periods[p]
            
            # Initial period constraints
            model.addConstr(inv_age[p, 0, 0] == initial_inventory.get(p, 0) + order[p, 0] - demands.get((p, 0), 0))
            for a in range(1, shelf_life):
                model.addConstr(inv_age[p, 0, a] == 0)
                
            # Subsequent periods
            for t in range(1, periods):
                # New inventory (age 0) comes from current period's order
                model.addConstr(inv_age[p, t, 0] == order[p, t])
                
                # Inventory aging and consumption
                for a in range(1, shelf_life):
                    # Previous period's inventory of age a-1 becomes age a
                    model.addConstr(inv_age[p, t, a] == inv_age[p, t-1, a-1])
                
                # Demand satisfaction constraint using all available inventory
                model.addConstr(gp.quicksum(inv_age[p, t-1, a] for a in range(shelf_life)) + 
                              order[p, t] >= demands.get((p, t), 0))
                
                # Ensure oldest inventory is used first (FIFO)
                for a in range(shelf_life-1):
                    model.addConstr(inv_age[p, t, a+1] <= inv_age[p, t, a])
        
        # Individual capacity constraints
        for p in range(products):
            for t in range(periods):
                model.addConstr(gp.quicksum(inv_age[p, t, a] 
                                          for a in range(expiration_periods[p])) <= capacities[p])
        
        # Shared warehouse capacity constraint
        if shared_capacity is not None:
            for t in range(periods):
                model.addConstr(gp.quicksum(gp.quicksum(inv_age[p, t, a] 
                                                       for a in range(expiration_periods[p]))
                                          for p in range(products)) <= shared_capacity)
        
        # Setup constraints
        M = {p: max(demands.get((p, t), 0) for t in range(periods)) * 2 for p in range(products)}
        for p in range(products):
            for t in range(periods):
                model.addConstr(order[p, t] <= M[p] * y[p, t])
        
        # Optimize
        model.optimize()
        
        # Check solution status
        if model.Status == GRB.OPTIMAL:
            # Extract results
            order_quantities = {(p, t): order[p, t].X for p in range(products) for t in range(periods)}
            inventory_levels = {(p, t): sum(inv_age[p, t, a].X for a in range(expiration_periods[p])) 
                              for p in range(products) for t in range(periods)}
            total_cost = model.ObjVal
            
            return order_quantities, inventory_levels, total_cost
        else:
            print(f"Optimization failed with status {model.Status}")
            return None, None, None
            
    except gp.GurobiError as e:
        print(f"Gurobi error: {e}")
        return None, None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

def print_solution(order_quantities, inventory_levels, total_cost, periods, products):
    """Print the solution in a formatted way"""
    if order_quantities is None or inventory_levels is None:
        print("No solution to display")
        return
        
    print("\nOptimal Solution:")
    print("-" * 70)
    print("Period | Product | Order Quantity | Inventory Level")
    print("-" * 70)
    
    for t in range(periods):
        for p in range(products):
            print(f"{t+1:6d} | {p+1:7d} | {order_quantities[p, t]:13.2f} | {inventory_levels[p, t]:15.2f}")
        print("-" * 70)
    print(f"\nTotal Cost: ${total_cost:,.2f}")

#  Example usage
if __name__ == "__main__":
  
    periods = 4
    products = 3
    
    # Demand for each product in each period
    demands = {
        (0, t): [10, 20, 15, 7][t] for t in range(periods)    # Product 0
    }
    demands.update({
        (1, t): [30, 45, 20, 15][t] for t in range(periods)   # Product 1
    })
    demands.update({
        (2, t): [19, 14, 20, 8][t] for t in range(periods)    # Product 2
    })
    
    # Costs and constraints
    holding_costs = {0: 2, 1: 3, 2: 2}          # Holding cost per unit per period
    ordering_costs = {0: 3, 1: 4, 2: 3}         # Cost per unit ordered
    setup_costs = {0: 100, 1: 120, 2: 110}      # Fixed cost per order
    capacities = {0: 150, 1: 160, 2: 70}          # Individual capacity limits
    shared_capacity = 150                       # Total warehouse capacity
    expiration_periods = {0: 1, 1: 1, 2: 1}     # Shelf life in periods
    
    # Initial Inventory: Provided as input (e.g., starting inventory for each product)
    initial_inventory = {0: 5, 1: 10, 2: 20}  # Only per product, not period-specific

    # Solve the problem
    orders, inventory, cost = solve_multi_product_inventory(
        periods=periods,
        products=products,
        demands=demands,
        holding_costs=holding_costs,
        ordering_costs=ordering_costs,
        setup_costs=setup_costs,
        capacities=capacities,
        expiration_periods=expiration_periods,
        shared_capacity=shared_capacity,
        initial_inventory=initial_inventory
    )
    
    # Display results
    print_solution(orders, inventory, cost, periods, products)    