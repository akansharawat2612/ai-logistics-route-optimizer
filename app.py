import streamlit as st
import joblib
import pandas as pd
import plotly.graph_objects as go

from src.smart_route_optimizer import (
    geocode_location,
    get_road_distance,
    get_road_geometry,
    optimize_route
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Logistics Route Optimizer",
    page_icon="🚚",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("🚚 AI Logistics Route Optimizer")

st.caption(
    "AI-powered delivery delay prediction and intelligent route optimization"
)


# =========================================================
# LOAD MODEL
# =========================================================

@st.cache_resource
def load_model():

    return joblib.load(
        "src/delay_model.pkl"
    )


try:

    model = load_model()

except Exception as e:

    st.error(
        "Could not load the delay prediction model."
    )

    st.write(e)

    st.stop()


# =========================================================
# SESSION STATE
# =========================================================

if "delivery_count" not in st.session_state:

    st.session_state.delivery_count = 1


# =========================================================
# LOCATIONS
# =========================================================

st.header("📍 Delivery Locations")


pickup = st.text_input(
    "🏭 Pickup / Warehouse",
    key="pickup_location"
)


st.subheader("🏠 Delivery Locations")


delivery_locations = []


for i in range(
    st.session_state.delivery_count
):

    location = st.text_input(
        f"Delivery Location {i + 1}",
        key=f"delivery_{i}"
    )

    delivery_locations.append(
        location.strip()
    )


# =========================================================
# ADD DELIVERY
# =========================================================

if st.button(
    "➕ Add delivery location",
    use_container_width=True
):

    st.session_state.delivery_count += 1

    st.rerun()


# =========================================================
# CONDITIONS
# =========================================================

st.header("🌦️ Delivery Conditions")


col1, col2, col3 = st.columns(3)


with col1:

    traffic = st.selectbox(
        "🚦 Traffic",
        [
            "Low",
            "Medium",
            "High"
        ]
    )


with col2:

    weather = st.selectbox(
        "🌧️ Weather",
        [
            "Clear",
            "Cloudy",
            "Rainy"
        ]
    )


with col3:

    vehicle = st.selectbox(
        "🚐 Vehicle",
        [
            "Bike",
            "Car",
            "Van",
            "Truck"
        ]
    )


col4, col5 = st.columns(2)


with col4:

    package_weight = st.number_input(
        "📦 Package Weight (kg)",
        min_value=0.0,
        value=10.0,
        step=1.0
    )


with col5:

    time_of_day = st.selectbox(
        "🕐 Time of Day",
        [
            "Morning",
            "Afternoon",
            "Evening",
            "Night"
        ]
    )


# =========================================================
# OPTIMIZE BUTTON
# =========================================================

st.write("")


optimize_button = st.button(
    "🚀 Optimize Delivery Route",
    use_container_width=True,
    type="primary"
)


# =========================================================
# OPTIMIZATION
# =========================================================

if optimize_button:

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not pickup.strip():

        st.error(
            "Please enter a pickup / warehouse location."
        )

        st.stop()


    valid_deliveries = [
        location
        for location in delivery_locations
        if location.strip()
    ]


    if len(valid_deliveries) == 0:

        st.error(
            "Please enter at least one delivery location."
        )

        st.stop()


    # -----------------------------------------------------
    # LOCATIONS
    # -----------------------------------------------------

    pickup_name = pickup.strip()

    location_names = [
        pickup_name
    ] + valid_deliveries


    # -----------------------------------------------------
    # GEOCODING
    # -----------------------------------------------------

    st.info(
        "📍 Finding locations and calculating real road routes..."
    )


    coordinates = {}

    progress = st.progress(0)

    failed = False


    for index, location in enumerate(
        location_names
    ):

        result = geocode_location(
            location
        )


        if result is None:

            st.error(
                f"❌ Could not find: {location}"
            )

            st.warning(
                "Try entering the location together "
                "with its city."
            )

            failed = True

            break


        coordinates[location] = result


        progress.progress(
            int(
                (
                    (index + 1)
                    / len(location_names)
                )
                * 100
            )
        )


    progress.empty()


    if failed:

        st.stop()


    # =====================================================
    # ML DISTANCE
    # =====================================================

    distances = []


    for delivery in valid_deliveries:

        distance = get_road_distance(
            pickup_name,
            delivery,
            coordinates
        )

        distances.append(
            distance
        )


    average_distance = (
        sum(distances) / len(distances)
        if distances
        else 0
    )


    # =====================================================
    # ML INPUT
    # =====================================================

    input_data = pd.DataFrame(
        {
            "distance_km": [
                average_distance
            ],

            "traffic": [
                traffic
            ],

            "weather": [
                weather
            ],

            "vehicle": [
                vehicle
            ],

            "package_weight_kg": [
                package_weight
            ],

            "time_of_day": [
                time_of_day
            ]
        }
    )


    # =====================================================
    # PREDICTION
    # =====================================================

    prediction_probability = (
        model.predict_proba(
            input_data
        )[0][1]
    )


    delay_prediction = model.predict(
        input_data
    )[0]


    delay_probability = float(
        prediction_probability
    )


    if delay_prediction == 1:

        prediction_text = "DELAYED"

    else:

        prediction_text = "ON TIME"


    # =====================================================
    # OPTIMIZE ROUTE
    # =====================================================

    route, route_cost = optimize_route(
        location_names,
        coordinates,
        traffic,
        weather,
        delay_probability
    )


    if not route:

        st.error(
            "Unable to calculate an optimized route."
        )

        st.stop()


    # =====================================================
    # ACTUAL ROAD DISTANCE
    # =====================================================

    total_distance = 0.0


    for i in range(
        len(route) - 1
    ):

        start = route[i]

        end = route[i + 1]


        distance = get_road_distance(
            start,
            end,
            coordinates
        )


        total_distance += distance


    # =====================================================
    # RESULTS
    # =====================================================

    st.divider()

    st.header("📊 Route Summary")


    metric1, metric2, metric3, metric4 = (
        st.columns(4)
    )


    with metric1:

        st.metric(
            "Delivery Stops",
            len(valid_deliveries)
        )


    with metric2:

        st.metric(
            "Total Road Distance",
            f"{total_distance:.2f} km"
        )


    with metric3:

        st.metric(
            "Delay Probability",
            f"{delay_probability * 100:.1f}%"
        )


    with metric4:

        if delay_prediction == 1:

            st.metric(
                "AI Prediction",
                "🔴 DELAYED"
            )

        else:

            st.metric(
                "AI Prediction",
                "🟢 ON TIME"
            )


    # =====================================================
    # ROUTE ORDER
    # =====================================================

    st.header("🧭 Optimized Route")


    for i, location in enumerate(route):

        if i == 0:

            st.write(
                f"🏭 **Pickup:** {location}"
            )

        else:

            st.write(
                f"➡️ **Delivery {i}:** {location}"
            )


    # =====================================================
    # MAP
    # =====================================================

    st.header("🗺️ Optimized Road Route")


    route_colors = [
        "#00E5FF",
        "#FF4B91",
        "#FFD166",
        "#7CFF6B",
        "#B388FF",
        "#FF8C42",
        "#00FFB3",
        "#FF6B6B",
        "#4D96FF",
        "#F72585"
    ]


    fig = go.Figure()


    # =====================================================
    # ROUTE LINES
    # =====================================================

    for i in range(
        len(route) - 1
    ):

        start = route[i]

        end = route[i + 1]


        geometry = get_road_geometry(
            start,
            end,
            coordinates
        )


        latitudes = [
            point[0]
            for point in geometry
        ]


        longitudes = [
            point[1]
            for point in geometry
        ]


        # The color corresponds to the
        # destination delivery.

        line_color = route_colors[
            i % len(route_colors)
        ]


        fig.add_trace(
            go.Scattermap(
                lat=latitudes,
                lon=longitudes,

                mode="lines",

                line=dict(
                    width=8,
                    color=line_color
                ),

                name=f"Delivery {i + 1}",

                hovertemplate=(
                    f"{start} → {end}"
                    "<extra></extra>"
                )
            )
        )


    # =====================================================
    # DELIVERY MARKERS
    # =====================================================

    for i, location in enumerate(
        valid_deliveries
    ):

        latitude, longitude = (
            coordinates[location]
        )


        marker_color = route_colors[
            i % len(route_colors)
        ]


        fig.add_trace(
            go.Scattermap(
                lat=[latitude],
                lon=[longitude],

                mode="markers+text",

                marker=dict(
                    size=17,
                    color=marker_color
                ),

                text=[
                    f"Delivery {i + 1}"
                ],

                textposition="top right",

                name=f"Delivery {i + 1}",

                hovertemplate=(
                    f"<b>Delivery {i + 1}</b>"
                    f"<br>{location}"
                    "<extra></extra>"
                ),

                showlegend=True
            )
        )


    # =====================================================
    # PICKUP MARKER
    # =====================================================

    warehouse_lat, warehouse_lon = (
        coordinates[pickup_name]
    )


    fig.add_trace(
        go.Scattermap(
            lat=[warehouse_lat],
            lon=[warehouse_lon],

            mode="markers+text",

            marker=dict(
                size=22,
                color="white"
            ),

            text=[
                "🏭 Pickup"
            ],

            textposition="bottom right",

            name="Pickup / Warehouse",

            hovertemplate=(
                f"<b>Pickup</b>"
                f"<br>{pickup_name}"
                "<extra></extra>"
            ),

            showlegend=True
        )
    )


    # =====================================================
    # MAP CENTER
    # =====================================================

    all_latitudes = [
        coordinates[location][0]
        for location in location_names
    ]


    all_longitudes = [
        coordinates[location][1]
        for location in location_names
    ]


    center_lat = (
        min(all_latitudes)
        + max(all_latitudes)
    ) / 2


    center_lon = (
        min(all_longitudes)
        + max(all_longitudes)
    ) / 2


    # =====================================================
    # MAP ZOOM
    # =====================================================

    max_range = max(
        max(all_latitudes) - min(all_latitudes),
        max(all_longitudes) - min(all_longitudes)
    )


    if max_range < 0.01:

        zoom_level = 14

    elif max_range < 0.03:

        zoom_level = 12

    elif max_range < 0.08:

        zoom_level = 10

    elif max_range < 0.2:

        zoom_level = 8

    else:

        zoom_level = 6


    # =====================================================
    # MAP
    # =====================================================

    fig.update_layout(

        map=dict(
            style="open-street-map",

            center=dict(
                lat=center_lat,
                lon=center_lon
            ),

            zoom=zoom_level
        ),

        height=650,

        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),

        paper_bgcolor="#0e1117",

        legend=dict(
            title="Route Legend",
            font=dict(
                color="white"
            ),
            bgcolor="#171b24"
        )
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # =====================================================
    # ROUTE LEGEND
    # =====================================================

    st.subheader("🎨 Route Legend")


    for i, location in enumerate(
        valid_deliveries
    ):

        color = route_colors[
            i % len(route_colors)
        ]


        st.markdown(
            f"""
            <span style="
                display:inline-block;
                width:16px;
                height:16px;
                background-color:{color};
                border-radius:50%;
                margin-right:8px;
            "></span>
            <b>Delivery {i + 1}</b> — {location}
            """,
            unsafe_allow_html=True
        )


    st.markdown(
        """
        <span style="
            display:inline-block;
            width:16px;
            height:16px;
            background-color:white;
            border-radius:50%;
            margin-right:8px;
        "></span>
        <b>Pickup / Warehouse</b>
        """,
        unsafe_allow_html=True
    )


    # =====================================================
    # CONDITIONS
    # =====================================================

    st.header("🌦️ Current Delivery Conditions")


    condition1, condition2, condition3 = (
        st.columns(3)
    )


    with condition1:

        st.markdown(
            "### 🚦 Traffic"
            )

        st.info(traffic)


    with condition2:

        st.markdown(
            "### 🌧️ Weather"
            )

        st.info(weather)


    with condition3:

        st.markdown(
            "### 🚐 Vehicle"
        )

        st.info(vehicle)


    # =====================================================
    # AI RISK
    # =====================================================

    st.header("🤖 AI Delay Risk Analysis")


    risk_data = pd.DataFrame(
        {
            "Status": [
                "On Time",
                "Delayed"
            ],

            "Probability": [
                1 - delay_probability,
                delay_probability
            ]
        }
    )


    fig_risk = go.Figure()


    fig_risk.add_trace(
        go.Bar(
            x=risk_data["Status"],

            y=(
                risk_data["Probability"]
                * 100
            ),

            text=[
                f"{value * 100:.1f}%"
                for value
                in risk_data["Probability"]
            ],

            textposition="auto"
        )
    )


    fig_risk.update_layout(
        yaxis_title="Probability (%)",

        yaxis_range=[
            0,
            100
        ],

        height=350,

        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20
        )
    )


    st.plotly_chart(
        fig_risk,
        use_container_width=True
    )


    # =====================================================
    # AI RECOMMENDATION
    # =====================================================

    st.header("💡 AI Recommendation")


    if delay_probability >= 0.70:

        st.warning(
            "⚠️ High delay risk detected. "
            "Consider leaving earlier, using an "
            "alternate route, or prioritizing "
            "these deliveries."
        )


    elif delay_probability >= 0.40:

        st.warning(
            "🟡 Moderate delay risk detected. "
            "Keep some additional delivery time "
            "as a buffer."
        )


    else:

        st.success(
            "🟢 Low delay risk detected. "
            "Current conditions appear suitable "
            "for the planned route."
        )


    # =====================================================
    # DISCLAIMER
    # =====================================================

    st.caption(
        "Note: The delay prediction model is trained "
        "on a synthetic dataset for demonstration "
        "and portfolio purposes."
    )