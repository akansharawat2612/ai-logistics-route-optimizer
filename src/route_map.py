import folium
from streamlit_folium import st_folium


# Demo coordinates for our logistics network
LOCATION_COORDINATES = {
    "Warehouse": (28.6139, 77.2090),
    "Customer A": (28.6250, 77.2150),
    "Customer B": (28.6050, 77.2250),
    "Customer C": (28.6200, 77.2350),
    "Customer D": (28.6000, 77.2150)
}


def display_route_map(route):

    if not route:
        return

    # Center map around warehouse
    warehouse = LOCATION_COORDINATES["Warehouse"]

    logistics_map = folium.Map(
        location=warehouse,
        zoom_start=13
    )

    route_coordinates = []

    # Add markers
    for location in route:

        coordinates = LOCATION_COORDINATES[location]

        route_coordinates.append(coordinates)

        if location == "Warehouse":
            icon_color = "red"
            icon_symbol = "home"
        else:
            icon_color = "blue"
            icon_symbol = "map-marker"

        folium.Marker(
            location=coordinates,
            popup=location,
            tooltip=location,
            icon=folium.Icon(
                color=icon_color,
                icon=icon_symbol
            )
        ).add_to(logistics_map)

    # Draw route
    folium.PolyLine(
        route_coordinates,
        weight=5,
        opacity=0.8
    ).add_to(logistics_map)

    # Display map
    st_folium(
        logistics_map,
        width=None,
        height=500
    )