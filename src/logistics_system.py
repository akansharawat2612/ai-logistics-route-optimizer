import joblib
import pandas as pd

from smart_route_optimizer import optimize_route


# Load trained ML model
model = joblib.load("src/delay_model.pkl")


print("======================================")
print("      AI LOGISTICS OPTIMIZER")
print("======================================")
print()


# Get delivery information
distance = float(input("Enter distance (km): "))
traffic = input("Enter traffic (Low/Medium/High): ").title()
weather = input("Enter weather (Clear/Cloudy/Rainy): ").title()
vehicle = input("Enter vehicle (Bike/Van/Truck): ").title()
weight = float(input("Enter package weight (kg): "))
time_of_day = input(
    "Enter time of day (Morning/Afternoon/Evening): "
).title()


# Create delivery data
delivery = pd.DataFrame([{
    "distance_km": distance,
    "traffic": traffic,
    "weather": weather,
    "vehicle": vehicle,
    "package_weight_kg": weight,
    "time_of_day": time_of_day
}])


# Predict delay
delay_probability = model.predict_proba(delivery)[0][1]
prediction = model.predict(delivery)[0]


print()
print("--------------------------------------")
print("        DELAY PREDICTION")
print("--------------------------------------")

print(
    f"Delay Probability: {delay_probability * 100:.1f}%"
)

if prediction == 1:
    print("Prediction: DELAYED")
else:
    print("Prediction: ON TIME")


# Optimize route using ML prediction
route, route_cost = optimize_route(
    traffic=traffic,
    weather=weather,
    delay_probability=delay_probability
)


print()
print("--------------------------------------")
print("        SMART ROUTE")
print("--------------------------------------")

if route:
    print("Recommended Route:")
    print(" -> ".join(route))

    print()
    print("Adjusted Route Cost:", route_cost)

else:
    print("No suitable route found.")


# Final recommendation
print()
print("--------------------------------------")
print("        FINAL RECOMMENDATION")
print("--------------------------------------")

if delay_probability >= 0.7:
    print("HIGH DELAY RISK")
    print("Consider using the recommended route.")

elif delay_probability >= 0.4:
    print("MODERATE DELAY RISK")
    print("Monitor traffic and weather conditions.")

else:
    print("LOW DELAY RISK")
    print("Delivery conditions look favorable.")

print()
print("======================================")