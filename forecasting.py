import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import matplotlib.pyplot as plt

df_rec = pd.read_csv('data_24_hours.csv', parse_dates=['timestamp'])
df_rec.sort_values('timestamp', inplace=True)


# Pre-process the data

df_rec['hour'] = df_rec['timestamp'].dt.hour
df_rec['sin_hour'] = np.sin(2 * np.pi * df_rec['hour'] / 24)
df_rec['cos_hour'] = np.cos(2 * np.pi * df_rec['hour'] / 24)


features = df_rec[['usage_cpu', 'usage_memory', 'sin_hour', 'cos_hour']].values


scaler = MinMaxScaler(feature_range=(0, 1))
scaled_features = scaler.fit_transform(features)

# sliding window of 10 timesteps to predict the next CPU usage.
window_size = 10
X = []
y = []  
for i in range(len(scaled_features) - window_size):
    X.append(scaled_features[i:i+window_size])
    y.append(scaled_features[i+window_size, 0])
X = np.array(X)
y = np.array(y)

print("X shape:", X.shape)  
print("y shape:", y.shape)  


model = Sequential()
model.add(LSTM(50, input_shape=(window_size, X.shape[2])))
model.add(Dense(1))  # Predicting CPU usage
model.compile(loss='mean_squared_error', optimizer='adam')


history = model.fit(X, y, epochs=20, batch_size=32, validation_split=0.1)

'''
plt.figure(figsize=(8, 4))
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss Over Epochs')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.show()
'''

model.save("lstm_cpu_usage_model.h5")


#TESTING

# Predict on the entire available data (using the sliding windows)
predictions = model.predict(X)

# Since our scaler was fitted on all features, we need to invert scaling manually for CPU usage.
# We use the min and max values for the CPU usage (first feature) from the scaler.
cpu_min = scaler.data_min_[0]
cpu_max = scaler.data_max_[0]

# Invert scaling: scaled_value = (value - min) / (max - min)
predictions_cpu = predictions.flatten() * (cpu_max - cpu_min) + cpu_min
actual_cpu = y * (cpu_max - cpu_min) + cpu_min

# Create a timestamp series that aligns with our predictions.
# The first prediction corresponds to the timestamp at index 'window_size' in df_rec.
timestamps_future = df_rec['timestamp'].iloc[window_size:].reset_index(drop=True)  # corresponds to actual CPU usage at t+10
timestamps_forecast = df_rec['timestamp'].iloc[:-window_size].reset_index(drop=True)  # corresponds to the time when forecast is made

plt.figure(figsize=(14, 6))
# Plot actual CPU usage at t+10
plt.plot(timestamps_future, actual_cpu, label="Actual CPU Usage (t+10)")
# Plot predicted CPU usage at the time of forecast (shifted left)
plt.plot(timestamps_forecast, predictions_cpu, label="Predicted CPU Usage (Forecast made at t)", linestyle="--")
plt.xlabel("Timestamp")
plt.ylabel("CPU Usage")
plt.title("Actual vs. Predicted CPU Usage")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()