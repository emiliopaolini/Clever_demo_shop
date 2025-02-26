import argparse
import threading, time, datetime, sys, requests
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt

# --- Function to collect resource data from the API ---
def collect_resources(stop_event, api_endpoint, interval_sec, data_list):
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


def main(run_duration):

    api_endpoint = "http://10.109.226.4:5000/clusters/cluster1/pods/resources"
    interval_sec = 2                    
    run_duration = 24 * 3600               
    window_size = 15                    
    forecast_horizon = 10               
    pod_filter = "recommendationservice"  
    
    
    collected_data = []    
    forecast_times = []    
    forecast_values = []   
    
    stop_event = threading.Event()
    collector_thread = threading.Thread(target=collect_resources, args=(stop_event, api_endpoint, interval_sec, collected_data))
    collector_thread.start()
    

    model = load_model("lstm_cpu_usage_model.h5")
    scaler = joblib.load("scaler.pkl")
    
    start_time = time.time()
    print("Real-time forecasting started...")
    
    while time.time() - start_time < run_duration:
        
        df = pd.DataFrame(collected_data)
        if df.empty:
            time.sleep(1)
            continue
        
        df = df[df["pod_name"].str.contains(pod_filter, case=False, na=False)]
        if df.empty or len(df) < window_size:
            time.sleep(1)
            continue
        

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
        forecast_times.append(forecast_time)
        forecast_values.append(pred_cpu)
        
        actual_cpu_time_t = float(window_df["usage_cpu"].iloc[-1])
        print(f"Forecast made at {forecast_time}: Predicted CPU (for t+forecast_horizon) = {pred_cpu:.2f}, Actual CPU at time t = {actual_cpu_time_t:.2f}")
        
        time.sleep(interval_sec)
    
    
    stop_event.set()
    collector_thread.join()
    
    print("Data collection and forecasting completed.")
    
    # --- Save Data ---
    df_actual = pd.DataFrame(collected_data)
    df_actual["timestamp"] = pd.to_datetime(df_actual["timestamp"])
    df_actual = df_actual[df_actual["pod_name"].str.contains(pod_filter, case=False, na=False)]
    df_actual = df_actual.sort_values("timestamp")
    df_actual.to_csv("actual_data.csv", index=False)
    
    
    df_forecast = pd.DataFrame({
        "timestamp": forecast_times,
        "predicted_cpu": forecast_values
    })
    df_forecast.to_csv("forecasts.csv", index=False)
    
    n = len(df_forecast)
    
    timestamps_pred = df_actual["timestamp"].iloc[window_size : window_size + n].reset_index(drop=True)

    delta = df_actual["timestamp"].diff().median()

    timestamps_pred_shifted = timestamps_pred - forecast_horizon * delta

    import matplotlib.pyplot as plt

    plt.figure(figsize=(14, 6))
    plt.plot(df_actual["timestamp"], df_actual["usage_cpu"], label="Actual CPU Usage", color="blue")
    plt.plot(timestamps_pred_shifted, df_forecast["predicted_cpu"], label="Forecasted CPU Usage (shifted)", linestyle="--", color="red")
    plt.xlabel("Timestamp")
    plt.ylabel("CPU Usage")
    plt.title("24-Hour Real-Time Actual vs Forecasted CPU Usage")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Forecasting Script")
    parser.add_argument("--run_duration", type=int, default=86400,
                        help="Run duration in seconds (default: 24 hours)")
    args = parser.parse_args()
    
    main(args.run_duration)