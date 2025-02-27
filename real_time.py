import os
import signal
import threading
import time
import datetime
import sys
import requests
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
#from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt

# Global stop event so the signal handler can trigger shutdown.
stop_event = None

def handle_sigterm(signum, frame):
    print("Received termination signal. Stopping gracefully...")
    if stop_event is not None:
        stop_event.set()

# Ignore SIGINT (Ctrl+C) so that only SIGTERM stops the script.
signal.signal(signal.SIGINT, lambda s, f: print("SIGINT ignored. Use SIGTERM to stop."))

def collect_resources(stop_event, api_endpoint, interval_sec, data_list):
    """Collects resource usage data at regular intervals."""
    while not stop_event.is_set():
        try:
            response = requests.get(api_endpoint)
            response.raise_for_status()
            resources = response.json()
            timestamp = datetime.datetime.now().isoformat()
            for res in resources:
                data_point = {
                    "timestamp": timestamp,
                    "node_id": res["node_id"],
                    "node_name": res["node_name"],
                    "pod_name": res["pod_name"],
                    "usage_cpu": res["usage_cpu"],
                    "usage_memory": res["usage_memory"]
                }
                data_list.append(data_point)
        except Exception as e:
            print(f"[Collector] Error fetching resources: {e}", file=sys.stderr)
        time.sleep(interval_sec)

def predict_cpu_usage(model, scaler, df, window_size, forecast_horizon):
    """Processes the collected data, applies transformations, and makes predictions."""
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    window_df = df.iloc[-window_size:].copy()
    window_df["hour"] = window_df["timestamp"].dt.hour
    window_df["sin_hour"] = np.sin(2 * np.pi * window_df["hour"] / 24)
    window_df["cos_hour"] = np.cos(2 * np.pi * window_df["hour"] / 24)

    base_date = window_df["timestamp"].iloc[0].replace(hour=0, minute=0, second=0, microsecond=0)
    window_df["timestamp_numeric"] = (window_df["timestamp"] - base_date).dt.total_seconds()

    features_window = window_df[["usage_cpu", "usage_memory", "sin_hour", "cos_hour", "timestamp_numeric"]].values
    scaled_window = scaler.transform(features_window)
    X_window = np.expand_dims(scaled_window, axis=0)

    pred = model.predict(X_window)

    cpu_min = scaler.data_min_[0]
    cpu_max = scaler.data_max_[0]
    pred_cpu = pred.flatten()[0] * (cpu_max - cpu_min) + cpu_min

    forecast_time = window_df["timestamp"].iloc[-1]
    actual_cpu_time_t = float(window_df["usage_cpu"].iloc[-1])

    print(f"Forecast made at {forecast_time}: Predicted CPU (for t+{forecast_horizon}) = {pred_cpu:.2f}, Actual CPU at time t = {actual_cpu_time_t:.2f}")

    return forecast_time, pred_cpu

def plot_results(df_actual, df_forecast, window_size, forecast_horizon):
    """Plots actual vs forecasted CPU usage."""
    timestamps_pred = df_actual["timestamp"].iloc[window_size : window_size + len(df_forecast)].reset_index(drop=True)
    delta = df_actual["timestamp"].diff().median()
    timestamps_pred_shifted = timestamps_pred - forecast_horizon * delta

    plt.figure(figsize=(14, 6))
    plt.plot(df_actual["timestamp"], df_actual["usage_cpu"], label="Actual CPU Usage", color="blue")
    plt.plot(timestamps_pred_shifted, df_forecast["predicted_cpu"], label="Forecasted CPU Usage (shifted)", linestyle="--", color="red")
    plt.xlabel("Timestamp")
    plt.ylabel("CPU Usage")
    plt.title("Real-Time Actual vs Forecasted CPU Usage")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def main():
    global stop_event
    # Read configuration from environment variables (with defaults if not set)
    API_ENDPOINT   = os.environ.get('API_ENDPOINT', 'http://10.109.226.4:5000/clusters/cluster1/pods/resources')
    INTERVAL_SEC   = int(os.environ.get('INTERVAL_SEC', '2'))
    WINDOW_SIZE    = int(os.environ.get('WINDOW_SIZE', '15'))
    FORECAST_HORIZON = int(os.environ.get('FORECAST_HORIZON', '10'))
    POD_FILTER     = os.environ.get('POD_FILTER', 'recommendationservice')
    MODEL_PATH     = os.environ.get('MODEL_PATH', 'LSTM_model')
    SCALER_PATH    = os.environ.get('SCALER_PATH', 'scaler.pkl')

    collected_data = []
    forecast_times = []
    forecast_values = []

    stop_event = threading.Event()
    # Register SIGTERM handler to enable graceful shutdown.
    signal.signal(signal.SIGTERM, handle_sigterm)

    collector_thread = threading.Thread(target=collect_resources, args=(stop_event, API_ENDPOINT, INTERVAL_SEC, collected_data))
    collector_thread.start()

    
    model = tf.keras.models.load_model(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    print("Real-time forecasting started (running indefinitely)...")

    try:
        while not stop_event.is_set():
            df = pd.DataFrame(collected_data)
            if df.empty:
                time.sleep(1)
                continue

            df = df[df["pod_name"].str.contains(POD_FILTER, case=False, na=False)]
            if df.empty or len(df) < WINDOW_SIZE:
                time.sleep(1)
                continue

            forecast_time, pred_cpu = predict_cpu_usage(model, scaler, df, WINDOW_SIZE, FORECAST_HORIZON)
            forecast_times.append(forecast_time)
            forecast_values.append(pred_cpu)
            time.sleep(INTERVAL_SEC)

    finally:
        print("Stopping data collection and forecasting...")
        stop_event.set()
        collector_thread.join()

        df_actual = pd.DataFrame(collected_data)
        df_actual["timestamp"] = pd.to_datetime(df_actual["timestamp"])
        df_actual = df_actual[df_actual["pod_name"].str.contains(POD_FILTER, case=False, na=False)]
        df_actual = df_actual.sort_values("timestamp")
        df_actual.to_csv("actual_data.csv", index=False)

        df_forecast = pd.DataFrame({"timestamp": forecast_times, "predicted_cpu": forecast_values})
        df_forecast.to_csv("forecasts.csv", index=False)

        
        print("Script exited gracefully.")

if __name__ == "__main__":
    main()