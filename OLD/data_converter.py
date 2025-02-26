import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read the CSV file (update the file name as needed)
df = pd.read_csv("data.csv")

# Filter for rows corresponding to the recommendation service pod
df_rec = df[df['pod_name'].str.contains("recommendationservice", case=False, na=False)].copy()

# Convert timestamp to datetime and sort
df_rec['timestamp'] = pd.to_datetime(df_rec['timestamp'])
df_rec.sort_values('timestamp', inplace=True)

# Compute elapsed seconds from the first measurement
df_rec['elapsed_sec'] = (df_rec['timestamp'] - df_rec['timestamp'].iloc[0]).dt.total_seconds()

# For simulation: assume the real data spans ~10 minutes, which we want to map to 24 hours.
# Scaling factor: 86400 seconds in 24 hours divided by the real elapsed seconds.
if df_rec['elapsed_sec'].iloc[-1] == 0:
    factor = 1  # safeguard for a single measurement
else:
    factor = 86400 / df_rec['elapsed_sec'].iloc[-1]

# Compute the simulated time in hours (0 to 24 hours)
df_rec['simulated_hours'] = (df_rec['elapsed_sec'] * factor) / 3600

# Create a new datetime column using the simulated hours.
# Use midnight on the day of the first timestamp as the base.
base_date = df_rec['timestamp'].iloc[0].replace(hour=0, minute=0, second=0, microsecond=0)
df_rec['simulated_timestamp'] = base_date + pd.to_timedelta(df_rec['simulated_hours'], unit='h')

# Plot CPU and Memory usage over simulated hours
fig, ax1 = plt.subplots(figsize=(10, 6))

color_cpu = 'tab:blue'
ax1.set_xlabel("Simulated Hours")
ax1.set_ylabel("CPU Usage", color=color_cpu)
line_cpu, = ax1.plot(df_rec['simulated_hours'], df_rec['usage_cpu'], marker='o', linestyle='-', color=color_cpu, label='CPU Usage')
ax1.tick_params(axis='y', labelcolor=color_cpu)

ax2 = ax1.twinx()
color_mem = 'tab:red'
ax2.set_ylabel("Memory Usage", color=color_mem)
line_mem, = ax2.plot(df_rec['simulated_hours'], df_rec['usage_memory'], marker='x', linestyle='--', color=color_mem, label='Memory Usage')
ax2.tick_params(axis='y', labelcolor=color_mem)

lines = [line_cpu, line_mem]
labels = [line.get_label() for line in lines]
ax1.legend(lines, labels, loc='upper left')
plt.title("Recommendation Service CPU and Memory Usage")
ax1.grid(True)
plt.tight_layout()
plt.show()

# Prepare final DataFrame with the desired structure:
# node_id, node_name, pod_name, usage_cpu, usage_memory, timestamp
df_final = df_rec[['node_id', 'node_name', 'pod_name', 'usage_cpu', 'usage_memory']].copy()
# Replace the original timestamp with the simulated timestamp
df_final['timestamp'] = df_rec['simulated_timestamp']

# Save the final dataset to CSV
df_final.to_csv("data_24_hours.csv", index=False)
print("Dataset saved to 'data_24_hours.csv'.")