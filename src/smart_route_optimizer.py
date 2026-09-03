import requests
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


# =========================================================
# GEOCODING
# =========================================================


def geocode_location(address):
    url = "https://nominatim.openstreetmap.org/search"

    search_queries = [
        address,
        f"{address}, Dehradun, Uttarakhand, India",
        f"{address}, Uttarakhand, India",
        f"{address}, India"
    ]

    headers = {
        "User-Agent": "AI-Logistics-Route-Optimizer/1.0"
    }

    for search_query in search_queries:
        params = {
            "q": search_query,
            "format": "json",
            "limit": 5,
            "countrycodes": "in",
            "addressdetails": 1
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=10
            )

            response.raise_for_status()
            data = response.json()

            if data:
                for result in data:
                    result_address = result.get("address", {})
                    country = result_address.get(
                        "country",
                        ""
                    ).lower()

                    if country == "india":
                        latitude = float(result["lat"])
                        longitude = float(result["lon"])

                        return latitude, longitude

        except Exception:
            continue

    return None


# =========================================================
# ROAD DISTANCE
# =========================================================

def get_road_distance(start, end, coordinates):

    start_lat, start_lon = coordinates[start]
    end_lat, end_lon = coordinates[end]

    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
        "?overview=false"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data["code"] == "Ok":

            distance_meters = (
                data["routes"][0]["distance"]
            )

            return distance_meters / 1000

    except Exception:
        pass

    return 10.0


# =========================================================
# ROAD GEOMETRY
# =========================================================

def get_road_geometry(start, end, coordinates):

    start_lat, start_lon = coordinates[start]
    end_lat, end_lon = coordinates[end]

    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
        "?overview=full&geometries=geojson"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data["code"] == "Ok":

            route_coordinates = (
                data["routes"][0]["geometry"]["coordinates"]
            )

            return [
                (latitude, longitude)
                for longitude, latitude
                in route_coordinates
            ]

    except Exception:
        pass

    return [
        coordinates[start],
        coordinates[end]
    ]


# =========================================================
# CREATE DISTANCE MATRIX
# =========================================================

def create_distance_matrix(locations, coordinates):

    matrix = []

    for start in locations:

        row = []

        for end in locations:

            if start == end:

                row.append(0)

            else:

                distance = get_road_distance(
                    start,
                    end,
                    coordinates
                )

                row.append(
                    int(distance * 1000)
                )

        matrix.append(row)

    return matrix


# =========================================================
# OPEN ROUTE OPTIMIZATION
# =========================================================

def optimize_route(
    locations,
    coordinates,
    traffic,
    weather,
    delay_probability
):

    if len(locations) < 2:

        return [], 0


    # =====================================================
    # REAL ROAD DISTANCES
    # =====================================================

    distance_matrix = create_distance_matrix(
        locations,
        coordinates
    )


    # =====================================================
    # TRAFFIC FACTORS
    # =====================================================

    traffic_factor = {
        "Low": 1.00,
        "Medium": 1.15,
        "High": 1.35
    }


    # =====================================================
    # WEATHER FACTORS
    # =====================================================

    weather_factor = {
        "Clear": 1.00,
        "Cloudy": 1.08,
        "Rainy": 1.20
    }


    traffic_multiplier = traffic_factor.get(
        traffic,
        1.00
    )


    weather_multiplier = weather_factor.get(
        weather,
        1.00
    )


    # =====================================================
    # AI RISK FACTOR
    # =====================================================

    risk_multiplier = (
        1 + (delay_probability * 0.10)
    )


    # =====================================================
    # ADJUST DISTANCE
    # =====================================================

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


    # =====================================================
    # ADD DUMMY END NODE
    # =====================================================
    #
    # This is the important part.
    #
    # The vehicle starts at location 0
    # (warehouse/pickup).
    #
    # It must visit every delivery.
    #
    # The dummy node acts as the END.
    #
    # Therefore the vehicle does NOT need
    # to travel back to the warehouse.
    #
    # =====================================================

    number_of_locations = len(locations)

    dummy_node = number_of_locations

    expanded_matrix = []

    for i in range(number_of_locations):

        row = adjusted_matrix[i].copy()

        # Zero cost to finish at dummy node
        row.append(0)

        expanded_matrix.append(row)


    # Dummy node row
    expanded_matrix.append(
        [0] * (number_of_locations + 1)
    )


    # =====================================================
    # OR-TOOLS
    # =====================================================

    manager = pywrapcp.RoutingIndexManager(
        number_of_locations + 1,
        1,
        [0],
        [dummy_node]
    )


    routing = pywrapcp.RoutingModel(
        manager
    )


    # =====================================================
    # DISTANCE CALLBACK
    # =====================================================

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

        return expanded_matrix[
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


    # =====================================================
    # SEARCH PARAMETERS
    # =====================================================

    search_parameters = (
        pywrapcp.DefaultRoutingSearchParameters()
    )


    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy
        .PATH_CHEAPEST_ARC
    )


    # =====================================================
    # SOLVE
    # =====================================================

    solution = routing.SolveWithParameters(
        search_parameters
    )


    if solution:

        route = []

        index = routing.Start(0)

        total_cost = 0


        while not routing.IsEnd(index):

            node_index = manager.IndexToNode(
                index
            )


            # Ignore dummy node
            if node_index < number_of_locations:

                route.append(
                    locations[node_index]
                )


            previous_index = index


            index = solution.Value(
                routing.NextVar(index)
            )


            total_cost += (
                routing.GetArcCostForVehicle(
                    previous_index,
                    index,
                    0
                )
            )


        return (
            route,
            round(total_cost / 1000, 2)
        )


    return [], 0