import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error, classification_report
import matplotlib.pyplot as plt
import snowflake.connector
from dotenv import load_dotenv
import os
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account="gsxalxt-hp10837",
    warehouse="COMPUTE_WH",
    database="SUPPLY_CHAIN_DB",
    schema="ANALYTICS"
)

# --- Load data from Snowflake ---
suppliers_df = pd.read_sql("SELECT * FROM MART_SUPPLIER_RISK", conn)
orders_df = pd.read_sql("SELECT * FROM STG_ORDERS", conn)
suppliers_df.columns = suppliers_df.columns.str.lower()
orders_df.columns = orders_df.columns.str.lower()

print("Data loaded from Snowflake.")

# ─────────────────────────────────────────
# MODEL 1: K-Means Clustering
# ─────────────────────────────────────────
features = ['otd_rate', 'lead_time_variance', 'defect_rate', 'order_volume']
X_cluster = suppliers_df[features].fillna(0)

# Elbow method
inertias = []
for k in range(2, 9):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_cluster)
    inertias.append(km.inertia_)

plt.figure(figsize=(8, 4))
plt.plot(range(2, 9), inertias, marker='o')
plt.title('Elbow Method — Optimal K')
plt.xlabel('Number of Clusters')
plt.ylabel('Inertia')
plt.savefig('data/processed/elbow_plot.png')
plt.close()

# Final model with K=4
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
suppliers_df['cluster'] = kmeans.fit_predict(X_cluster)

cluster_map = {
    suppliers_df.groupby('cluster')['otd_rate'].mean().idxmax(): 'Reliable Partner',
    suppliers_df.groupby('cluster')['lead_time_variance'].mean().idxmax(): 'Delivery Risk',
    suppliers_df.groupby('cluster')['defect_rate'].mean().idxmax(): 'Cost Risk',
}
remaining = [c for c in range(4) if c not in cluster_map]
if remaining:
    cluster_map[remaining[0]] = 'Critical Watch'

suppliers_df['cluster_label'] = suppliers_df['cluster'].map(cluster_map)
print("\nK-Means Cluster Distribution:")
print(suppliers_df['cluster_label'].value_counts())

# ─────────────────────────────────────────
# MODEL 2: Linear Regression — Demand Forecasting (rolling features)
# ─────────────────────────────────────────
orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
orders_df['month'] = orders_df['order_date'].dt.month
orders_df['year'] = orders_df['order_date'].dt.year
orders_df['quarter'] = orders_df['order_date'].dt.quarter

le = LabelEncoder()
orders_df['category_encoded'] = le.fit_transform(orders_df['product_category'])

# Aggregate monthly demand per category
demand_df = orders_df.groupby(['year', 'month', 'quarter', 'category_encoded']).agg(
    total_demand=('quantity_ordered', 'sum')
).reset_index().sort_values(['category_encoded', 'year', 'month'])

# Rolling lag features
demand_df['lag_1'] = demand_df.groupby('category_encoded')['total_demand'].shift(1)
demand_df['lag_2'] = demand_df.groupby('category_encoded')['total_demand'].shift(2)
demand_df['rolling_mean_3'] = demand_df.groupby('category_encoded')['total_demand'].transform(
    lambda x: x.shift(1).rolling(3).mean()
)
demand_df = demand_df.dropna()

X_demand = demand_df[['month', 'quarter', 'category_encoded', 'lag_1', 'lag_2', 'rolling_mean_3']]
y_demand = demand_df['total_demand']

X_train, X_test, y_train, y_test = train_test_split(X_demand, y_demand, test_size=0.2, random_state=42)
lr = LinearRegression()
lr.fit(X_train, y_train)
y_pred = lr.predict(X_test)
mape = mean_absolute_percentage_error(y_test, y_pred) * 100
print(f"\nDemand Forecast MAPE: {mape:.2f}%")

demand_df['forecast'] = lr.predict(X_demand)

# ─────────────────────────────────────────
# MODEL 3: Naive Bayes — Disruption Risk (fixed class imbalance)
# ─────────────────────────────────────────
from sklearn.utils import resample

le_zone = LabelEncoder()
le_payment = LabelEncoder()
suppliers_df['zone_encoded'] = le_zone.fit_transform(suppliers_df['location_zone'])
suppliers_df['payment_encoded'] = le_payment.fit_transform(suppliers_df['payment_terms'])
suppliers_df['otd_bucket'] = pd.cut(suppliers_df['otd_rate'], bins=[0, 0.65, 0.80, 1.0], labels=[0, 1, 2])
suppliers_df['lt_var_bucket'] = pd.cut(suppliers_df['lead_time_variance'], bins=[0, 3, 7, 100], labels=[0, 1, 2])
suppliers_df['disruption_risk'] = suppliers_df['risk_label'].map({
    'Critical Watch': 'High',
    'Delivery Risk': 'High',
    'Cost Risk': 'Medium',
    'Reliable Partner': 'Low'
})

nb_features = ['zone_encoded', 'payment_encoded', 'otd_bucket', 'lt_var_bucket']
X_nb = suppliers_df[nb_features].astype(float)
y_nb = suppliers_df['disruption_risk']

# Oversample minority classes
df_nb = X_nb.copy()
df_nb['target'] = y_nb.values
majority = df_nb[df_nb.target == 'Low']
medium = resample(df_nb[df_nb.target == 'Medium'], replace=True, n_samples=len(majority), random_state=42)
high = resample(df_nb[df_nb.target == 'High'], replace=True, n_samples=len(majority), random_state=42)
df_balanced = pd.concat([majority, medium, high])

X_bal = df_balanced[nb_features]
y_bal = df_balanced['target']

X_train_nb, X_test_nb, y_train_nb, y_test_nb = train_test_split(X_bal, y_bal, test_size=0.2, random_state=42)
nb = GaussianNB()
nb.fit(X_train_nb, y_train_nb)
y_pred_nb = nb.predict(X_test_nb)
print("\nNaive Bayes Classification Report:")
print(classification_report(y_test_nb, y_pred_nb))

suppliers_df['risk_score'] = nb.predict_proba(X_nb).max(axis=1).round(4)
suppliers_df['predicted_risk'] = nb.predict(X_nb)

# ─────────────────────────────────────────
# Write ML results back to Snowflake
# ─────────────────────────────────────────
cursor = conn.cursor()
cursor.execute("USE DATABASE SUPPLY_CHAIN_DB")
cursor.execute("USE SCHEMA ANALYTICS")
cursor.execute("""
    CREATE OR REPLACE TABLE MART_ML_OUTPUTS (
        supplier_id STRING,
        supplier_name STRING,
        location_zone STRING,
        cluster_label STRING,
        predicted_risk STRING,
        risk_score FLOAT,
        otd_rate FLOAT,
        lead_time_variance FLOAT,
        defect_rate FLOAT,
        order_volume NUMBER
    )
""")

ml_output = suppliers_df[[
    'supplier_id', 'supplier_name', 'location_zone',
    'cluster_label', 'predicted_risk', 'risk_score',
    'otd_rate', 'lead_time_variance', 'defect_rate', 'order_volume'
]].fillna('Unknown')

data_to_insert = [tuple(row) for row in ml_output.itertuples(index=False)]
cursor.executemany("""
    INSERT INTO MART_ML_OUTPUTS VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", data_to_insert)

conn.commit()
cursor.close()
conn.close()

ml_output.to_csv('data/processed/ml_outputs.csv', index=False)
print("\nML results written to Snowflake and saved locally.")