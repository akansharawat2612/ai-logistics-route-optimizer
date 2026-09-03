import streamlit as st
import joblib
import pandas as pd
import plotly.graph_objects as go

from src.smart_route_optimizer import (
    optimize_route,
    get_road_geometry
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Logistics Optimizer",
    page_icon="🚚",
    layout="wide"
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #9ca3af;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 24px;
        font-weight: 600;
        margin-top: 20px;
    }

    .route-box {
        padding: 22px;
        border-radius: 12px;
        border: 1px solid #333842;
        background-color: #17191f;
        margin-top: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# LOAD MACHINE LEARNING MODEL
# ============================================================

model = joblib.load("src/delay_model.pkl")


# ============================================================
# LOCATION COORDINATES
# ============================================================

coordinates = {
    "Warehouse": (30.3165, 78.0322),
    "ISBT Dehradun": (30.2850, 78.0080),
    "Clock Tower": (30.3256, 78.0437),
    "Prem Nagar": (30.3510, 77.9630),
    "Rajpur Road": (30.3600, 78.0800)
}


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🚚 AI Logistics Optimizer</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-powered delivery delay prediction and smart route optimization'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# ============================================================
# DELIVERY INFORMATION
# ============================================================

st.markdown(
    '<div class="section-title">📦 Delivery Information</div>',
    unsafe_allow_html=True
)

st.write("Enter the details of the delivery below.")

col1, col2 = st.columns(2)


with col1:

    distance = st.number_input(
        "Distance (km)",
        min_value=1.0,
        max_value=500.0,
        value=75.0
    )

    traffic = st.selectbox(
        "Traffic",
        ["Low", "Medium", "High"]
    )

    weather = st.selectbox(
        "Weather",
        ["Clear", "Cloudy", "Rainy"]
    )


with col2:

    vehicle = st.selectbox(
        "Vehicle",
        ["Bike", "Van", "Truck"]
    )

    weight = st.number_input(
        "Package Weight (kg)",
        min_value=0.5,
        max_value=100.0,
        value=15.0
    )

    time_of_day = st.selectbox(
        "Time of Day",
        ["Morning", "Afternoon", "Evening"]
    )


st.write("")


# ============================================================
# OPTIMIZE BUTTON
# ============================================================

optimize = st.button(
    "🚀 Optimize Delivery",
    use_container_width=True
)


# ============================================================
# RUN AI SYSTEM
# ============================================================

if optimize:

    delivery = pd.DataFrame(
        [
            {
                "distance_km": distance,
                "traffic": traffic,
                "weather": weather,
                "vehicle": vehicle,
                "package_weight_kg": weight,
                "time_of_day": time_of_day
            }
        ]
    )


    # ========================================================
    # ML PREDICTION
    # ========================================================

    delay_probability = model.predict_proba(delivery)[0][1]

    prediction = model.predict(delivery)[0]


    # ========================================================
    # ROUTE OPTIMIZATION
    # ========================================================

    route, route_cost = optimize_route(
        traffic=traffic,
        weather=weather,
        delay_probability=delay_probability
    )


    # ========================================================
    # ROUTE MAP
    # ========================================================

    st.markdown(
        '<div class="section-title">🗺️ Optimized Route Map</div>',
        unsafe_allow_html=True
    )

    # Get actual road geometry from OSRM
    road_latitudes = []
    road_longitudes = []

    for i in range(len(route) - 1):

        start = route[i]
        end = route[i + 1]

        road_points = get_road_geometry(start, end)

        for latitude, longitude in road_points:
            road_latitudes.append(latitude)
            road_longitudes.append(longitude)


    # Create map
    fig = go.Figure()


    # ========================================================
    # ACTUAL ROAD ROUTE
    # ========================================================

    fig.add_trace(
        go.Scattermap(
            lat=road_latitudes,
            lon=road_longitudes,
            mode="lines",
            line=dict(width=5),
            name="Optimized Route"
        )
    )


    # ========================================================
    # LOCATION MARKERS
    # ========================================================

    marker_latitudes = []
    marker_longitudes = []
    marker_labels = []

    for location in route:

        latitude, longitude = coordinates[location]

        marker_latitudes.append(latitude)
        marker_longitudes.append(longitude)
        marker_labels.append(location)


    fig.add_trace(
        go.Scattermap(
            lat=marker_latitudes,
            lon=marker_longitudes,
            mode="markers+text",
            marker=dict(size=12),
            text=marker_labels,
            textposition="top right",
            hoverinfo="text",
            name="Locations"
        )
    )


    # ========================================================
    # MAP SETTINGS
    # ========================================================

    fig.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(
                lat=30.32,
                lon=78.03
            ),
            zoom=11
        ),
        height=550,
        margin=dict(
            l=0,
            r=0,
            t=0,
            b=0
        ),
        showlegend=True
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # ========================================================
    # ROUTE DETAILS
    # ========================================================

    st.markdown("### 🛣️ Optimized Route")

    if route:

        route_text = " → ".join(route)

        st.info(
            f"**{route_text}**"
        )

        st.caption(
            f"Total optimized route cost: {route_cost}"
        )

    else:

        st.error("No suitable route found.")


    # ========================================================
    # DELIVERY ANALYSIS
    # ========================================================

    st.markdown(
        '<div class="section-title">📊 Delivery Analysis</div>',
        unsafe_allow_html=True
    )


    prediction_text = (
        "DELAYED"
        if prediction == 1
        else "ON TIME"
    )


    result1, result2, result3 = st.columns(3)


    with result1:

        st.metric(
            "🎯 Delay Probability",
            f"{delay_probability * 100:.1f}%"
        )


    with result2:

        st.metric(
            "🤖 ML Prediction",
            prediction_text
        )


    with result3:

        st.metric(
            "🛣️ Route Cost",
            route_cost
        )


    st.write("")


    # ========================================================
    # RISK ASSESSMENT
    # ========================================================

    if delay_probability >= 0.7:

        st.error(
            "🔴 HIGH DELAY RISK\n\n"
            "The AI model predicts a high probability of delay. "
            "The smart route has been optimized for the current conditions."
        )

    elif delay_probability >= 0.4:

        st.warning(
            "🟠 MODERATE DELAY RISK\n\n"
            "There is a moderate possibility of delay. "
            "Keep an eye on traffic and weather conditions."
        )

    else:

        st.success(
            "🟢 LOW DELAY RISK\n\n"
            "Current delivery conditions look favorable."
        )


    # ========================================================
    # RECOMMENDED ROUTE
    # ========================================================

    st.markdown(
        '<div class="section-title">📍 Recommended Route</div>',
        unsafe_allow_html=True
    )


    if route:

        st.markdown(
            '<div class="route-box">',
            unsafe_allow_html=True
        )

        for i, location in enumerate(route):

            if location == "Warehouse":
                icon = "🏭"
            else:
                icon = "📍"

            st.markdown(
                f"### {icon} {location}"
            )

            if i < len(route) - 1:
                st.markdown("⬇️")

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    else:

        st.error("No suitable route found.")


    st.write("")


    # ========================================================
    # DELIVERY CONDITIONS
    # ========================================================

    st.markdown(
        '<div class="section-title">🚦 Delivery Conditions</div>',
        unsafe_allow_html=True
    )


    info1, info2, info3, info4 = st.columns(4)


    with info1:

        st.metric(
            "Traffic",
            traffic
        )


    with info2:

        st.metric(
            "Weather",
            weather
        )


    with info3:

        st.metric(
            "Vehicle",
            vehicle
        )


    with info4:

        st.metric(
            "Distance",
            f"{distance:.1f} km"
        )


    # ========================================================
    # DELIVERY INSIGHTS
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">💡 Delivery Insights</div>',
        unsafe_allow_html=True
    )

    st.write(
        "The following operational signals are based on the "
        "current delivery conditions."
    )


    insight1, insight2 = st.columns(2)


    # ========================================================
    # TRAFFIC INSIGHT
    # ========================================================

    with insight1:

        if traffic == "High":
            traffic_risk = "🔴 High"
        elif traffic == "Medium":
            traffic_risk = "🟠 Medium"
        else:
            traffic_risk = "🟢 Low"

        st.metric(
            "🚦 Traffic Risk",
            traffic_risk
        )


    # ========================================================
    # WEATHER INSIGHT
    # ========================================================

    with insight2:

        if weather == "Rainy":
            weather_risk = "🔴 High"
        elif weather == "Cloudy":
            weather_risk = "🟠 Medium"
        else:
            weather_risk = "🟢 Low"

        st.metric(
            "🌦️ Weather Risk",
            weather_risk
        )


    insight3, insight4 = st.columns(2)


    # ========================================================
    # DISTANCE INSIGHT
    # ========================================================

    with insight3:

        if distance > 60:
            distance_risk = "🔴 Long"
        elif distance > 30:
            distance_risk = "🟠 Moderate"
        else:
            distance_risk = "🟢 Short"

        st.metric(
            "📏 Distance",
            f"{distance:.1f} km"
        )

        st.caption(
            f"Distance category: {distance_risk}"
        )


    # ========================================================
    # PACKAGE WEIGHT INSIGHT
    # ========================================================

    with insight4:

        if weight > 20:
            weight_risk = "🔴 Heavy"
        elif weight > 10:
            weight_risk = "🟠 Medium"
        else:
            weight_risk = "🟢 Light"

        st.metric(
            "📦 Package Weight",
            f"{weight:.1f} kg"
        )

        st.caption(
            f"Weight category: {weight_risk}"
        )


        # ========================================================
    # DELAY RISK VISUALIZATION
    # ========================================================

    st.write("")

    st.markdown("### ⚠️ Overall Delay Risk")

    st.progress(
        int(delay_probability * 100)
    )

    st.write(
        f"Current estimated delay probability: "
        f"**{delay_probability * 100:.1f}%**"
    )


    # ========================================================
    # RISK FACTOR OVERVIEW
    # ========================================================

    st.markdown("### 📊 Risk Factor Overview")

    # Convert operational conditions into risk scores
    traffic_score = {
        "Low": 20,
        "Medium": 55,
        "High": 90
    }[traffic]

    weather_score = {
        "Clear": 20,
        "Cloudy": 50,
        "Rainy": 85
    }[weather]

    if distance > 60:
        distance_score = 90
    elif distance > 30:
        distance_score = 55
    else:
        distance_score = 20

    if weight > 20:
        weight_score = 90
    elif weight > 10:
        weight_score = 55
    else:
        weight_score = 20

    ai_score = int(delay_probability * 100)


    # Create chart
    risk_fig = go.Figure()

    risk_fig.add_trace(
        go.Bar(
            x=[
                "Traffic",
                "Weather",
                "Distance",
                "Package Weight",
                "AI Delay Risk"
            ],
            y=[
                traffic_score,
                weather_score,
                distance_score,
                weight_score,
                ai_score
            ],
            text=[
                f"{traffic_score}%",
                f"{weather_score}%",
                f"{distance_score}%",
                f"{weight_score}%",
                f"{ai_score}%"
            ],
            textposition="auto"
        )
    )

    risk_fig.update_layout(
        yaxis=dict(
            title="Risk Score",
            range=[0, 100]
        ),
        xaxis_title="Operational Factor",
        height=400,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20
        )
    )

    st.plotly_chart(
        risk_fig,
        use_container_width=True
    )


    # ========================================================
    # FINAL RECOMMENDATION
    # ========================================================

    st.markdown("### 🧠 AI Recommendation")

    if delay_probability >= 0.7:

        st.warning(
            "The system recommends prioritizing this delivery. "
            "High-risk conditions may increase the chance of delay."
        )

    elif delay_probability >= 0.4:

        st.info(
            "The delivery has moderate operational risk. "
            "Monitoring traffic and weather conditions is recommended."
        )

    else:

        st.success(
            "The delivery currently has relatively low operational risk."
        )