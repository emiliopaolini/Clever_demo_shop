import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.pyplot as plt

# ----- Load and Preprocess Training Data -----
df_train = pd.read_csv("./data/recommendationservice_24_hours_training.csv", parse_dates=["timestamp"])
df_train.sort_values("timestamp", inplace=True)

# Create time-based features: hour, sin_hour, cos_hour.
df_train["hour"] = df_train["timestamp"].dt.hour
df_train["sin_hour"] = np.sin(2 * np.pi * df_train["hour"] / 24)
df_train["cos_hour"] = np.cos(2 * np.pi * df_train["hour"] / 24)

# Create a numeric timestamp feature: seconds since midnight.
base_date = df_train["timestamp"].iloc[0].replace(hour=0, minute=0, second=0, microsecond=0)
df_train["timestamp_numeric"] = (df_train["timestamp"] - base_date).dt.total_seconds()

# Prepare features (inputs) and target:
# Features: usage_cpu, usage_memory, sin_hour, cos_hour, timestamp_numeric.
# Target: CPU usage (the first feature), but forecasted forecast_horizon steps ahead.
features = df_train[["usage_cpu", "usage_memory", "sin_hour", "cos_hour", "timestamp_numeric"]].values

# ----- Scale the Features -----
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_features = scaler.fit_transform(features)
# Save the scaler for later use.
joblib.dump(scaler, "scaler.pkl")

# ----- Create Sliding Windows -----
window_size = 15
forecast_horizon = 10

X = []
y = []
for i in range(len(scaled_features) - window_size - forecast_horizon):
    X.append(scaled_features[i:i+window_size])
    # Target is the CPU usage (first feature) forecast_horizon steps ahead of the window end.
    y.append(scaled_features[i+window_size+forecast_horizon, 0])
X = np.array(X)
y = np.array(y)

print("Training data shape, X:", X.shape, "y:", y.shape)

# ----- Build and Train the LSTM Model -----
model = Sequential()
model.add(LSTM(100, input_shape=(window_size, X.shape[2])))
model.add(Dense(1))  # Predicting CPU usage.
model.compile(loss="mean_squared_error", optimizer="adam")

history = model.fit(X, y, epochs=20, batch_size=64, validation_split=0.1)
model.save("./LSTM_model", save_format="tf")


# ----- (Optional) Plot Training History -----
plt.figure(figsize=(8,4))
plt.plot(history.history["loss"], label="Train Loss")
plt.plot(history.history["val_loss"], label="Validation Loss")
plt.title("Training Loss")
plt.legend()
plt.show()

print("Training complete. Model saved as 'LSTM_model' and scaler as 'scaler.pkl'.")