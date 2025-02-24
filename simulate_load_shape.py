import math
import random
import matplotlib.pyplot as plt

class DiurnalShapeTester:
    def __init__(self, 
                 total_run_time=86400, 
                 base_users=50, 
                 peak_user_add=30, 
                 random_noise_range=5):
        self.total_run_time = total_run_time
        self.base_users = base_users
        self.peak_user_add = peak_user_add
        self.random_noise_range = random_noise_range
        self.scaling_param = int(86400 / self.total_run_time)

    def tick(self, run_time):
        if run_time > self.total_run_time:
            return None
        
        scaled_run_time = run_time * self.scaling_param
        
        current_minute = (scaled_run_time // 60) % 1440

        peak1 = math.exp(-((current_minute - 720)**2) / (2 * 120**2))
        peak2 = 0.5 * math.exp(-((current_minute - 1080)**2) / (2 * 120**2))

        noise = random.uniform(-self.random_noise_range, self.random_noise_range)

        user_count = self.base_users + self.peak_user_add * (peak1 + peak2) + noise

        if user_count < 0:
            user_count = 0

        user_count = int(user_count)

        spawn_rate = user_count

        return (user_count, spawn_rate)

def main():
    shape = DiurnalShapeTester(
        total_run_time=86400,
        base_users=50,
        peak_user_add=200,
        random_noise_range=5
    )

    results = []

    for t in range(shape.total_run_time + 1):
        tick_result = shape.tick(t)
        if tick_result is None:
            break
        user_count, spawn_rate = tick_result
        results.append((t, user_count))
    
    times = [r[0] for r in results]
    user_counts = [r[1] for r in results]

    plt.figure(figsize=(10, 5))
    plt.plot(times, user_counts, label="User Count")
    plt.title("Simulated Diurnal Load Shape Over Time")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Number of Users")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("num_users.png")

if __name__ == "__main__":
    main()
