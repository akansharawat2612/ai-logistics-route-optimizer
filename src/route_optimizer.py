from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp


# Distance between locations
distance_matrix = [
    [0, 10, 15, 20, 12],
    [10, 0, 35, 25, 18],
    [15, 35, 0, 30, 20],
    [20, 25, 30, 0, 14],
    [12, 18, 20, 14, 0]
]

locations = [
    "Warehouse",
    "Customer A",
    "Customer B",
    "Customer C",
    "Customer D"
]


# Create routing model
manager = pywrapcp.RoutingIndexManager(
    len(distance_matrix),
    1,
    0
)

routing = pywrapcp.RoutingModel(manager)


# Calculate distance between locations
def distance_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)

    return distance_matrix[from_node][to_node]


transit_callback_index = routing.RegisterTransitCallback(
    distance_callback
)

routing.SetArcCostEvaluatorOfAllVehicles(
    transit_callback_index
)


# Search for the best route
search_parameters = pywrapcp.DefaultRoutingSearchParameters()

search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
)


solution = routing.SolveWithParameters(search_parameters)


# Display the route
if solution:
    index = routing.Start(0)

    route = []
    total_distance = 0

    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        route.append(locations[node])

        previous_index = index
        index = solution.Value(routing.NextVar(index))

        total_distance += routing.GetArcCostForVehicle(
            previous_index,
            index,
            0
        )

    route.append(locations[manager.IndexToNode(index)])

    print("Best Route:")
    print(" -> ".join(route))

    print("\nTotal Distance:", total_distance, "km")

else:
    print("No route found.")