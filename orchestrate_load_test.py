import subprocess, threading
import time, datetime
import requests
import csv
import sys

import matplotlib.pyplot as plt
import pandas as pd

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

def run_locust(locust_command):
    print(f"[Locust] Starting Locust with command:\n  {locust_command}\n")
    process = subprocess.Popen(locust_command, shell=True)
    process.wait()
    print(f"[Locust] Locust process finished with return code {process.returncode}")

def save_data_to_csv(data_list, csv_out):
    fieldnames = ["timestamp", "node_id", "node_name", "pod_name", "usage_cpu", "usage_memory"]
    with open(csv_out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data_list:
            writer.writerow(row)

def plot_usage(data_list, plot_png=None):
    if not data_list:
        print("[Plot] No data to plot.")
        return

    df = pd.DataFrame(data_list)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values(by="timestamp", inplace=True)

    cpu_pivot = df.pivot_table(
        index="timestamp",
        columns="pod_name",
        values="usage_cpu",
        aggfunc="mean"
    )

    plt.figure(figsize=(12, 6))
    cpu_pivot.plot(ax=plt.gca())
    plt.title("CPU Usage Over Time by Pod")
    plt.xlabel("Time")
    plt.ylabel("CPU (millicores)")
    plt.tight_layout()

    if plot_png:
        plt.savefig(plot_png)
        print(f"[Plot] Saved plot to {plot_png}")
    else:
        plt.show()

def main():

    data_list = []
    stop_event = threading.Event()

    api_endpoint = "http://10.109.226.4:5000/clusters/cluster1/pods/resources"
    interval_sec = 2
    locust_cmd = "locust -f locustfile.py --host=http://10.103.178.157:80 --headless 2>&1"
    csv_out = 'data.csv'
    plot_out = 'plot.png'

    collector_thread = threading.Thread(
        target=collect_resources,
        args=(stop_event, api_endpoint, interval_sec, data_list),
        daemon=True
    )
    collector_thread.start()
    print("[Main] Collector thread started.")

    run_locust(locust_cmd)

    print("[Main] Locut exited")
    time.sleep(10)

    stop_event.set()
    collector_thread.join()
    print("[Main] Collector thread stopped.")

    save_data_to_csv(data_list, csv_out)
    print(f"[Main] Usage data saved to {csv_out}")

    plot_usage(data_list, plot_out)

if __name__ == "__main__":
    main()
