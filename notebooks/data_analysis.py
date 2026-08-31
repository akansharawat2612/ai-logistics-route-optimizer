import pandas as pd

# Load the dataset
df = pd.read_csv("data/delivery_data.csv")

# Show first 5 rows
print("First 5 deliveries:")
print(df.head())

# Show information about the dataset
print("\nDataset information:")
print(df.info())

# Check for missing values
print("\nMissing values:")
print(df.isnull().sum())

# Count delayed and non-delayed deliveries
print("\nDelivery status:")
print(df["delayed"].value_counts())
