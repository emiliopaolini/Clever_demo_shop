import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt

# ----- Load and Preprocess Test Data -----
df_rec = pd.read_csv("./data/recommendationservice_10MIN_testing.csv", parse_dates=["timestamp"])
df_rec.sort_values("timestamp", inplace=True)

# Create time-based features: hour, sin_hour, cos_hour.
df_rec["hour"] = df_rec["timestamp"].dt.hour
df_rec["sin_hour"] = np.sin(2 * np.pi * df_rec["hour"] / 24)
df_rec["cos_hour"] = np.cos(2 * np.pi * df_rec["hour"] / 24)

# Create a numeric timestamp feature: seconds since midnight.
base_date = df_rec["timestamp"].iloc[0].replace(hour=0, minute=0, second=0, microsecond=0)
df_rec["timestamp_numeric"] = (df_rec["timestamp"] - base_date).dt.total_seconds()

# Prepare features in the same order as during training.
features = df_rec[["usage_cpu", "usage_memory", "sin_hour", "cos_hour", "timestamp_numeric"]].values

# ----- Load the Saved Scaler and Scale the Features -----
scaler = joblib.load("scaler.pkl")
scaled_features = scaler.transform(features)

# ----- Define Sliding Window and Forecast Horizon -----
window_size = 15       
forecast_horizon = 10

# Build sliding windows for X and targets y.
X = []
y = []
for i in range(len(scaled_features) - window_size - forecast_horizon):
    X.append(scaled_features[i:i+window_size])
    # Target: CPU usage (first feature) at t + forecast_horizon.
    y.append(scaled_features[i+window_size+forecast_horizon, 0])
X = np.array(X)
y = np.array(y)

# Number of predictions (n)
n = len(y)
print("Number of predictions:", n)

# ----- Load the Trained Model and Make Predictions -----
model = load_model("lstm_cpu_usage_model.h5")
predictions = model.predict(X)

# Invert scaling for CPU usage (first feature) using the scaler parameters.
cpu_min = scaler.data_min_[0]
cpu_max = scaler.data_max_[0]
predictions_cpu = predictions.flatten() * (cpu_max - cpu_min) + cpu_min
# (For actual values we use y inverted—but for plotting actual, we use the original test data)
actual_cpu = y * (cpu_max - cpu_min) + cpu_min

# ----- Align Timestamps for Plotting -----
# We want to plot predictions at the time the forecast is made.
# The first forecast is available at index 'window_size'.
# Extract n timestamps starting at window_size.
timestamps_pred = df_rec["timestamp"].iloc[window_size: window_size+n].reset_index(drop=True)

# Compute the median time delta between consecutive samples.
delta = df_rec["timestamp"].diff().median()

# Shift the forecast timestamps left by forecast_horizon * delta.
# This plots the forecast at the time it was made rather than the time it refers to.
timestamps_pred_shifted = timestamps_pred - forecast_horizon * delta

# ----- Plot Actual vs. Predicted CPU Usage -----
plt.figure(figsize=(14, 6))
# Plot the full actual CPU usage from the test data.
plt.plot(df_rec["timestamp"], df_rec["usage_cpu"], label="Actual CPU Usage", color="blue")
# Overlay the predicted CPU usage at the shifted forecast timestamps.
plt.plot(timestamps_pred_shifted, predictions_cpu, label="Predicted CPU Usage (forecast made at t)", linestyle="--", color="red")
plt.xlabel("Timestamp")
plt.ylabel("CPU Usage")
plt.title("Actual vs. Predicted CPU Usage")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()