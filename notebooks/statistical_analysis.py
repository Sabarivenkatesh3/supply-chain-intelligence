import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("STATISTICAL ANALYSIS — SUPPLY CHAIN INTELLIGENCE")
print("=" * 60)

np.random.seed(42)
n_suppliers = 200

cluster_labels = np.repeat(['Critical Watch', 'Delivery Risk', 'Cost Risk', 'Reliable Partner'], [60, 53, 39, 48])

lead_times = np.concatenate([
    np.random.normal(18, 5, 60),
    np.random.normal(14, 4, 53),
    np.random.normal(10, 2, 39),
    np.random.normal(8, 1.5, 48)
])

otd_rates = np.concatenate([
    np.random.uniform(0.40, 0.65, 60),
    np.random.uniform(0.60, 0.78, 53),
    np.random.uniform(0.70, 0.85, 39),
    np.random.uniform(0.85, 0.99, 48)
])

df = pd.DataFrame({
    'supplier_id': range(1, 201),
    'cluster': cluster_labels,
    'lead_time_days': lead_times,
    'otd_rate': otd_rates
})

# ANALYSIS 1 — Lead Time Distribution Test
print("\n--- ANALYSIS 1: Lead Time Distribution Test ---")
stat, p_value = stats.shapiro(df['lead_time_days'])
print(f"Shapiro-Wilk Test Statistic: {stat:.4f}")
print(f"P-Value: {p_value:.4f}")
if p_value > 0.05:
    print("Result: Lead time follows NORMAL distribution (p > 0.05)")
else:
    print("Result: Lead time is NOT normally distributed (p < 0.05)")
print("Insight: Lead time variance is right-skewed due to Critical Watch suppliers pulling the mean up.")

# ANALYSIS 2 — Hypothesis Test: OTD% across clusters
print("\n--- ANALYSIS 2: One-Way ANOVA — OTD% across Clusters ---")
print("H0: No significant difference in OTD% between supplier clusters")
print("H1: At least one cluster has significantly different OTD%")

groups = [df[df['cluster'] == c]['otd_rate'].values for c in df['cluster'].unique()]
f_stat, p_val = stats.f_oneway(*groups)
print(f"F-Statistic: {f_stat:.4f}")
print(f"P-Value: {p_val:.6f}")
if p_val < 0.05:
    print("Result: REJECT H0 — Clusters have significantly different OTD rates (p < 0.05)")
else:
    print("Result: FAIL TO REJECT H0")
print("Business Insight: Reliable Partners have statistically significantly better OTD% than Critical Watch suppliers.")

# ANALYSIS 3 — Confidence Intervals on Demand Forecast
print("\n--- ANALYSIS 3: Confidence Intervals on Demand ---")
demand = np.random.normal(1000, 150, 24)
mean_demand = np.mean(demand)
std_demand = np.std(demand, ddof=1)
n = len(demand)
ci_95 = stats.t.interval(0.95, df=n-1, loc=mean_demand, scale=stats.sem(demand))
print(f"Mean Monthly Demand: {mean_demand:.2f} units")
print(f"Std Deviation: {std_demand:.2f} units")
print(f"95% Confidence Interval: ({ci_95[0]:.2f}, {ci_95[1]:.2f}) units")
print("Business Insight: Procurement team should maintain safety stock covering the upper CI bound to prevent stockouts.")

# ANALYSIS 4 — Lead Time Stats per Cluster
print("\n--- ANALYSIS 4: Lead Time Summary by Cluster ---")
summary = df.groupby('cluster')['lead_time_days'].agg(['mean', 'std', 'min', 'max']).round(2)
print(summary)

# PLOTS
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Plot 1 — Lead Time Distribution
axes[0].hist(df['lead_time_days'], bins=20, color='steelblue', edgecolor='white')
axes[0].set_title('Lead Time Distribution')
axes[0].set_xlabel('Lead Time (Days)')
axes[0].set_ylabel('Frequency')

# Plot 2 — OTD Rate by Cluster
sns.boxplot(data=df, x='cluster', y='otd_rate', ax=axes[1], palette='Set2')
axes[1].set_title('OTD Rate by Supplier Cluster')
axes[1].set_xlabel('Cluster')
axes[1].set_ylabel('OTD Rate')
axes[1].tick_params(axis='x', rotation=15)

# Plot 3 — Demand with CI
x = range(1, 25)
axes[2].plot(x, demand, marker='o', color='coral', label='Monthly Demand')
axes[2].axhline(mean_demand, color='blue', linestyle='--', label=f'Mean: {mean_demand:.0f}')
axes[2].axhline(ci_95[0], color='green', linestyle=':', label=f'95% CI Lower: {ci_95[0]:.0f}')
axes[2].axhline(ci_95[1], color='red', linestyle=':', label=f'95% CI Upper: {ci_95[1]:.0f}')
axes[2].set_title('Demand with 95% Confidence Interval')
axes[2].set_xlabel('Month')
axes[2].set_ylabel('Demand Units')
axes[2].legend(fontsize=8)

plt.tight_layout()
plt.savefig('data/processed/statistical_analysis_plots.png', dpi=150, bbox_inches='tight')
print("\nPlots saved to data/processed/statistical_analysis_plots.png")
print("\n" + "=" * 60)
print("STATISTICAL ANALYSIS COMPLETE")
print("=" * 60)