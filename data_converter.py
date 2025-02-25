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

# For simulation: the real data spans ~10 minutes, which we want to map to 24 hours.
# Scaling factor: 86400 seconds in 24 hours divided by the real elapsed seconds.
if df_rec['elapsed_sec'].iloc[-1] == 0:
    factor = 1  # safeguard for a single measurement
else:
    factor = 86400 / df_rec['elapsed_sec'].iloc[-1]

# Compute the simulated time in hours
df_rec['simulated_hours'] = (df_rec['elapsed_sec'] * factor) / 3600

# Create the plot with two y-axes
fig, ax1 = plt.subplots(figsize=(10, 6))

# Plot CPU usage on the primary y-axis (left)
color_cpu = 'tab:blue'
ax1.set_xlabel("Hours")
ax1.set_ylabel("CPU Usage", color=color_cpu)
line_cpu, = ax1.plot(df_rec['simulated_hours'], df_rec['usage_cpu'], marker='o', linestyle='-', color=color_cpu, label='CPU Usage')
ax1.tick_params(axis='y', labelcolor=color_cpu)

# Create a secondary y-axis for memory usage
ax2 = ax1.twinx()
color_mem = 'tab:red'
ax2.set_ylabel("Memory Usage", color=color_mem)
line_mem, = ax2.plot(df_rec['simulated_hours'], df_rec['usage_memory'], marker='x', linestyle='--', color=color_mem, label='Memory Usage')
ax2.tick_params(axis='y', labelcolor=color_mem)

# Combine legends from both axes
lines = [line_cpu, line_mem]
labels = [line.get_label() for line in lines]
ax1.legend(lines, labels, loc='upper left')

# Title and grid
plt.title("Recommendation Service CPU and Memory Usage")
ax1.grid(True)

# Show the plot
plt.tight_layout()
plt.show()


df_rec.to_csv("data_24_hours.csv", index=False)