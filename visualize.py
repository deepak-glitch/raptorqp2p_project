import numpy as np
import matplotlib.pyplot as plt

# Synthetic data based on reported metrics
np.random.seed(42)
baseline_times = np.random.normal(loc=51.6, scale=5, size=200)
raptor_times = np.random.normal(loc=42.3, scale=4, size=200)

# Figure 1: Download Completion Time CDF
baseline_sorted = np.sort(baseline_times)
raptor_sorted = np.sort(raptor_times)
baseline_cdf = np.arange(1, len(baseline_sorted) + 1) / len(baseline_sorted)
raptor_cdf = np.arange(1, len(raptor_sorted) + 1) / len(raptor_sorted)

plt.figure(figsize=(6,4))
plt.plot(baseline_sorted, baseline_cdf, label='Baseline BitTorrent')
plt.plot(raptor_sorted, raptor_cdf, label='RaptorQP2P')
plt.xlabel('Completion Time (s)')
plt.ylabel('CDF')
plt.title('Figure 1: Download Completion Time Distribution')
plt.legend()
plt.tight_layout()
plt.show()

# Figure 2: Stall Events Distribution
baseline_stalls = np.random.poisson(lam=5.2, size=200)
raptor_stalls = np.random.poisson(lam=3.1, size=200)

plt.figure(figsize=(6,4))
plt.hist(baseline_stalls, alpha=0.7, bins=range(0, max(baseline_stalls.max(), raptor_stalls.max()) + 2), label='Baseline BitTorrent')
plt.hist(raptor_stalls, alpha=0.7, bins=range(0, max(baseline_stalls.max(), raptor_stalls.max()) + 2), label='RaptorQP2P')
plt.xlabel('Number of Stall Events per Session')
plt.ylabel('Frequency')
plt.title('Figure 2: Stall Events Distribution')
plt.legend()
plt.tight_layout()
plt.show()

# Figure 3: Upload Link Utilization
labels = ['Baseline BitTorrent', 'RaptorQP2P']
utilization = [0.68, 0.90]

plt.figure(figsize=(4,4))
plt.bar(labels, utilization)
plt.ylim(0, 1)
plt.ylabel('Fraction of Time > 80% Upload Usage')
plt.title('Figure 3: Upload Link Utilization')
plt.tight_layout()
plt.show()
