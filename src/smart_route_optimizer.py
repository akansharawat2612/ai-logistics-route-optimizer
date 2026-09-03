import requests
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


# ============================================================
# DEHRADUN LOCATIONS
# ============================================================

locations = [
    "Warehouse",
    "ISBT Dehradun",
    "Clock Tower",
    "Prem Nagar",
    "Rajpur Road"
]


# Coordinates: latitude, longitude
coordinates = {
    "Warehouse": (30.3165, 78.0322),
    "ISBT Dehradun": (30.2850, 78.0080),
    "Clock Tower": (30.3256, 78.0437),
    "Prem Nagar": (30.3510, 77.9630),
    "Rajpur Road": (30.3600, 78.0800)
}


# ============================================================
# GET ROAD DISTANCE FROM OSRM
# ============================================================

def get_road_distance(start, end):

    start_lat, start_lon = coordinates[start]
    end_lat, end_lon = coordinates[end]

    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
        f"?overview=false"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        data = response.json()

        if data["code"] == "Ok":

            distance_km = (
                data["routes"][0]["distance"] / 1000
            )

            return distance_km

    except Exception:

        pass

    # Fallback if OSRM is unavailable
    return 10.0


# ============================================================
# GET ACTUAL ROAD GEOMETRY FROM OSRM
# ============================================================

def get_road_geometry(start, end):

    start_lat, start_lon = coordinates[start]
    end_lat, end_lon = coordinates[end]

    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
        f"?overview=full&geometries=geojson"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        data = response.json()

        if data["code"] == "Ok":

            route_coordinates = (
                data["routes"][0]["geometry"]["coordinates"]
            )

            # OSRM returns:
            # [longitude, latitude]

            return [
                (latitude, longitude)
                for longitude, latitude in route_coordinates
            ]

    except Exception:

        pass

    # Fallback to straight line
    return [
        coordinates[start],
        coordinates[end]
    ]


# ============================================================
# CREATE ROAD DISTANCE MATRIX
# ============================================================

def create_distance_matrix():

    matrix = []

    for start in locations:

        row = []

        for end in locations:

            if start == end:

                row.append(0)

            else:

                distance = get_road_distance(
                    start,
                    end
                )

                # Convert km → metres
                row.append(
                    int(distance * 1000)
                )

        matrix.append(row)

    return matrix


# ============================================================
# ROUTE OPTIMIZATION
# ============================================================

def optimize_route(
    traffic,
    weather,
    delay_probability
):

    # Get actual road distances
    distance_matrix = create_distance_matrix()


    # --------------------------------------------------------
    # TRAFFIC FACTORS
    # --------------------------------------------------------

    traffic_factor = {

        "Low": 1.0,

        "Medium": 1.15,

        "High": 1.35

    }


    # --------------------------------------------------------
    # WEATHER FACTORS
    # --------------------------------------------------------

    weather_factor = {

        "Clear": 1.0,

        "Cloudy": 1.08,

        "Rainy": 1.20

    }


    traffic_multiplier = traffic_factor.get(
        traffic,
        1.0
    )

    weather_multiplier = weather_factor.get(
        weather,
        1.0
    )


    # --------------------------------------------------------
    # DELAY RISK FACTOR
    # --------------------------------------------------------

    risk_multiplier = (
        1 + (delay_probability * 0.10)
    )


    # --------------------------------------------------------
    # ADJUST DISTANCE MATRIX
    # --------------------------------------------------------

    adjusted_matrix = []

    for row in distance_matrix:

        adjusted_row = []

        for distance in row:

            adjusted_distance = (

                distance
                * traffic_multiplier
                * weather_multiplier
                * risk_multiplier

            )

            adjusted_row.append(
                int(adjusted_distance)
            )

        adjusted_matrix.append(
            adjusted_row
        )


    # ========================================================
    # OR-TOOLS ROUTING MODEL
    # ========================================================

    manager = pywrapcp.RoutingIndexManager(

        len(locations),

        1,

        0

    )


    routing = pywrapcp.RoutingModel(
        manager
    )


    # --------------------------------------------------------
    # DISTANCE CALLBACK
    # --------------------------------------------------------

    def distance_callback(
        from_index,
        to_index
    ):

        from_node = manager.IndexToNode(
            from_index
        )

        to_node = manager.IndexToNode(
            to_index
        )

        return adjusted_matrix[
            from_node
        ][
            to_node
        ]


    transit_callback_index = (
        routing.RegisterTransitCallback(
            distance_callback
        )
    )


    routing.SetArcCostEvaluatorOfAllVehicles(
        transit_callback_index
    )


    # --------------------------------------------------------
    # SEARCH PARAMETERS
    # --------------------------------------------------------

    search_parameters = (
        pywrapcp.DefaultRoutingSearchParameters()
    )


    search_parameters.first_solution_strategy = (

        routing_enums_pb2
        .FirstSolutionStrategy
        .PATH_CHEAPEST_ARC

    )


    # ========================================================
    # SOLVE
    # ========================================================

    solution = routing.SolveWithParameters(
        search_parameters
    )


    if solution:

        route = []

        index = routing.Start(0)


        while not routing.IsEnd(index):

            node_index = (
                manager.IndexToNode(index)
            )

            route.append(
                locations[node_index]
            )

            index = solution.Value(
                routing.NextVar(index)
            )


        # Return to warehouse
        route.append(
            locations[
                manager.IndexToNode(index)
            ]
        )


        total_cost = (
            solution.ObjectiveValue()
            / 1000
        )


        return (
            route,
            round(total_cost, 2)
        )


    return [], 0