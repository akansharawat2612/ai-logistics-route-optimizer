import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# Load the dataset
df = pd.read_csv("data/delivery_data.csv")


# Features and target
X = df.drop("delayed", axis=1)
y = df["delayed"]


# Categorical and numerical columns
categorical_columns = [
    "traffic",
    "weather",
    "vehicle",
    "time_of_day"
]

numerical_columns = [
    "distance_km",
    "package_weight_kg"
]


# Convert categorical data into numbers
preprocessor = ColumnTransformer(
    transformers=[
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_columns),
        ("numerical", "passthrough", numerical_columns)
    ]
)


# Create the model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)


# Create complete pipeline
pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ]
)


# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# Train the model
pipeline.fit(X_train, y_train)


# Make predictions
y_pred = pipeline.predict(X_test)


# Check accuracy
accuracy = accuracy_score(y_test, y_pred)

print("Model Training Complete!")
print()
print("Accuracy:", accuracy)
print()
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Save the trained model
joblib.dump(pipeline, "src/delay_model.pkl")

print("\nModel saved successfully!")