import numpy as np
import time
from datetime import datetime
import requests
import random
import argparse

class APICallSimulator:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/') + '/'  # ensure trailing slash
        # Endpoint weights
        self.endpoints = {
            'index': 1,
            'setCurrency': 2,
            'browseProduct': 10,
            'addToCart': 2,
            'viewCart': 3,
            'checkout': 1
        }
        
        # Calculate probabilities from weights
        total_weight = sum(self.endpoints.values())
        self.probabilities = {k: v/total_weight for k, v in self.endpoints.items()}
        
    def calculate_rate(self, x):
        """Calculate the current rate based on the diurnal pattern with random peak shifts and noise."""
        # Compute minute-of-day (x modulo 1440)
        minutes_of_day = x - np.floor(x / 1440) * 1440
        
        # Generate slight random shifts for each peak (in minutes)
        shift1 = random.uniform(-10, 10)  # shift for the first peak (around 12:00)
        shift2 = random.uniform(-10, 10)  # shift for the second peak (around 18:00)
        
        # First peak centered at 720 + shift1 minutes (12:00 plus random offset)
        peak1 = np.exp(-((minutes_of_day - (720 + shift1))**2) / (2 * 120**2))
        # Second peak centered at 1080 + shift2 minutes (18:00 plus random offset)
        peak2 = 0.5 * np.exp(-((minutes_of_day - (1080 + shift2))**2) / (2 * 120**2))
        
        # Generate random noise in the range [-5, 5]
        noise = random.random() * 10 - 5
        
        # Calculate the rate: base 50 plus scaled peaks and noise
        rate = 50 + 30 * (peak1 + peak2) + noise
        return max(0, rate)  # Ensure non-negative rate

    def select_endpoint(self):
        """Select an endpoint based on probabilities."""
        return random.choices(
            list(self.endpoints.keys()),
            weights=list(self.probabilities.values())
        )[0]

    def simulate_api_call(self, endpoint):
        """Simulate an API call (replace with actual API endpoints)."""
        full_url = f"{self.base_url}{endpoint}"
        try:
            # Uncomment the next line to perform an actual API call:
            # response = requests.get(full_url)
            print(f"Called endpoint: {full_url} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"Error calling {endpoint}: {str(e)}")

    def run(self, duration_minutes=1440):  # Run for 24 hours by default
        start_time = time.time()
        minute_counter = 0

        while minute_counter < duration_minutes:
            current_minute = (time.time() - start_time) / 60
            current_rate = self.calculate_rate(current_minute)
            
            # Convert rate per minute to delay in seconds
            delay = 60 / current_rate if current_rate > 0 else 60
            
            # Select and call endpoint
            endpoint = self.select_endpoint()
            self.simulate_api_call(endpoint)
            
            time.sleep(delay)
            minute_counter = int(current_minute)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="API Call Simulator")
    parser.add_argument(
        "--base_url", 
        type=str, 
        required=True,
        help="The base URL for API calls (e.g., http://your-api-endpoint.com/)"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        default=1440,
        help="Duration to run the simulation in minutes (default: 1440)"
    )
    
    args = parser.parse_args()
    
    simulator = APICallSimulator(args.base_url)
    simulator.run(duration_minutes=args.duration)