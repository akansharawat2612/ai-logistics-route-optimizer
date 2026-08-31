import pandas as pd
import numpy as np

np.random.seed(42)

n = 1000

data = {
    "distance_km": np.random.uniform(2, 100, n),
    "traffic": np.random.choice(
        ["Low", "Medium", "High"],
        n,
        p=[0.3, 0.45, 0.25]
    ),
    "weather": np.random.choice(
        ["Clear", "Cloudy", "Rainy"],
        n,
        p=[0.5, 0.3, 0.2]
    ),
    "vehicle": np.random.choice(
        ["Bike", "Van", "Truck"],
        n
    ),
    "package_weight_kg": np.random.uniform(0.5, 30, n),
    "time_of_day": np.random.choice(
        ["Morning", "Afternoon", "Evening"],
        n
    )
}

df = pd.DataFrame(data)

delay_score = (
    (df["distance_km"] > 60).astype(int) * 2
    + (df["traffic"] == "High").astype(int) * 3
    + (df["traffic"] == "Medium").astype(int)
    + (df["weather"] == "Rainy").astype(int) * 2
    + (df["package_weight_kg"] > 20).astype(int)
    + (df["time_of_day"] == "Evening").astype(int)
)

random_factor = np.random.randint(0, 3, n)
delay_score = delay_score + random_factor

df["delayed"] = (delay_score >= 4).astype(int)

df.to_csv("data/delivery_data.csv", index=False)

print("Dataset created successfully!")
print()
print(df.head())
print()
print("Total deliveries:", len(df))
print("Delayed deliveries:", df["delayed"].sum())