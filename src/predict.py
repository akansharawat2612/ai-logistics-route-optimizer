import pandas as pd
import joblib

# Load the trained model
model = joblib.load("src/delay_model.pkl")

# Example of a new delivery
new_delivery = pd.DataFrame({
    "distance_km": [75],
    "traffic": ["High"],
    "weather": ["Rainy"],
    "vehicle": ["Van"],
    "package_weight_kg": [15],
    "time_of_day": ["Evening"]
})

# Make prediction
prediction = model.predict(new_delivery)

# Get probability of delay
probability = model.predict_proba(new_delivery)[0][1]

print("New Delivery:")
print(new_delivery)

print("\nDelay Probability:", round(probability * 100, 2), "%")

if prediction[0] == 1:
    print("Prediction: DELAYED")
else:
    print("Prediction: ON TIME")
    