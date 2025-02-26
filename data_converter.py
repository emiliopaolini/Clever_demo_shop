import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
# Read the CSV file into a DataFrame.
# Replace 'data.csv' with your actual filename.
df = pd.read_csv('./data/data.csv')

# Filter rows to include only the recommendation service pod.
df = df[df['pod_name'].str.contains('recommendationservice')]

# Convert the 'timestamp' column to datetime objects.
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Get the minimum and maximum timestamp in the filtered data.
t_min = df['timestamp'].min()
t_max = df['timestamp'].max()

# Define the new start and end times:
# new_start is midnight on the day of t_min.
new_start = t_min.replace(hour=0, minute=0, second=0, microsecond=0)
# new_end is midnight the next day.
new_end = new_start + timedelta(days=1)

# Calculate the total duration of the new interval (24 hours).
new_duration = new_end - new_start

# Calculate the original duration.
original_duration = t_max - t_min

# Define a function to linearly rescale each timestamp.
def rescale_timestamp(t):
    # Calculate the fraction of time elapsed in the original interval.
    fraction = (t - t_min) / original_duration
    # Map this fraction to the new time interval.
    return new_start + fraction * new_duration

# Apply the rescaling to each timestamp.
df['new_timestamp'] = df['timestamp'].apply(rescale_timestamp)

# Optionally, drop the old timestamp column and rename new_timestamp.
# If you want to compare, you might keep both columns.
df_transformed = df.copy()
df_transformed = df_transformed.drop(columns=['timestamp'])
df_transformed = df_transformed.rename(columns={'new_timestamp': 'timestamp'})

# Print the transformed DataFrame with the new timestamps.
print(df_transformed)

# Save the transformed DataFrame to a new CSV file.
df_transformed.to_csv('recommendationservice_transformed.csv', index=False)

print("Transformation complete. The new CSV file is 'recommendationservice_transformed.csv'.")

# Plotting CPU usage vs new timestamps
plt.figure(figsize=(10, 6))
plt.plot(df['new_timestamp'], df['usage_cpu'], marker='o', linestyle='-', color='blue', label='CPU Usage')
plt.xlabel('Rescaled Timestamp')
plt.ylabel('CPU Usage')
plt.title('CPU Usage Over Rescaled Time for Recommendation Service Pod')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()