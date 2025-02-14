import numpy as np
import matplotlib.pyplot as plt

def load_function_with_noise_and_random_peaks(x):
    """
    Compute the load function including:
      - Random noise in [-5, 5]
      - Slight random shifts in the peak centers (±10 minutes)
      
    f(x) = 50 + 30 * (exp(-(((x mod 1440) - (720 + shift1))^2 / (2*120^2))) +
                      0.5 * exp(-(((x mod 1440) - (1080 + shift2))^2 / (2*120^2))))
           + noise
    """
    # Compute minute-of-day (x modulo 1440)
    minutes_of_day = x - np.floor(x / 1440) * 1440

    # Generate slight random shifts for each peak (in minutes)
    shift1 = np.random.uniform(-10, 10)  # shift for the first peak (around noon)
    shift2 = np.random.uniform(-10, 10)  # shift for the second peak (around 6:00 PM)
    
    # First peak centered at 720 + shift1 minutes (12:00 noon plus a slight random offset)
    peak1 = np.exp(-((minutes_of_day - (720 + shift1))**2) / (2 * 120**2))
    # Second peak centered at 1080 + shift2 minutes (6:00 PM plus a slight random offset)
    peak2 = 0.5 * np.exp(-((minutes_of_day - (1080 + shift2))**2) / (2 * 120**2))
    
    # Generate random noise uniformly distributed between -5 and 5 for each x value
    noise = np.random.uniform(-5, 5, size=x.shape)
    
    return 50 + 30 * (peak1 + peak2) + noise

# Generate x values (minutes over one day)
x_values = np.linspace(0, 1440*4, 1000)
y_values = load_function_with_noise_and_random_peaks(x_values)

plt.figure(figsize=(10, 5))
plt.plot(x_values, y_values, label='Load with Noise & Random Peaks', color='blue')
plt.xlabel("Minutes of Day")
plt.ylabel("Load (calls per minute)")
plt.title("Simulated Diurnal Load Function with Random Noise and Peak Variability")
plt.legend()
plt.grid(True)
plt.show()