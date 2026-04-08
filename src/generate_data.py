import pandas as pd
import numpy as np
from faker import Faker
import os

fake = Faker('en_IN')
np.random.seed(42)

# --- Suppliers ---
zones = ['North', 'South', 'East', 'West', 'Central']
payment_terms = ['Net30', 'Net60', 'Immediate', 'Net45']

suppliers = []
for i in range(200):
    suppliers.append({
        'supplier_id': f'SUP{i+1:03d}',
        'supplier_name': fake.company(),
        'location_zone': np.random.choice(zones),
        'payment_terms': np.random.choice(payment_terms),
        'otd_rate': round(np.random.uniform(0.50, 0.99), 2),
        'lead_time_avg': np.random.randint(5, 30),
        'lead_time_variance': round(np.random.uniform(0.5, 10.0), 2),
        'defect_rate': round(np.random.uniform(0.01, 0.20), 2),
        'order_volume': np.random.randint(100, 5000)
    })

suppliers_df = pd.DataFrame(suppliers)

# --- Orders ---
categories = ['Packaging', 'Raw Material', 'Chemicals', 'Electronics', 'Logistics']
orders = []
for i in range(2000):
    supplier = suppliers_df.sample(1).iloc[0]
    order_date = fake.date_between(start_date='-2y', end_date='-1d')
    lead_days = int(supplier['lead_time_avg'] + np.random.normal(0, supplier['lead_time_variance']))
    lead_days = max(1, lead_days)
    promised_date = order_date + pd.Timedelta(days=supplier['lead_time_avg'])
    delivery_date = order_date + pd.Timedelta(days=lead_days)

    orders.append({
        'order_id': f'ORD{i+1:05d}',
        'product_id': f'PRD{np.random.randint(1,50):03d}',
        'supplier_id': supplier['supplier_id'],
        'order_date': order_date,
        'delivery_date': delivery_date,
        'promised_date': promised_date,
        'quantity_ordered': np.random.randint(50, 1000),
        'quantity_received': np.random.randint(40, 1000),
        'unit_price': round(np.random.uniform(10, 500), 2),
        'product_category': np.random.choice(categories),
        'region': supplier['location_zone']
    })

orders_df = pd.DataFrame(orders)

os.makedirs('data/raw', exist_ok=True)
suppliers_df.to_csv('data/raw/suppliers.csv', index=False)
orders_df.to_csv('data/raw/orders.csv', index=False)

print("Data generated successfully!")
print(f"Suppliers: {len(suppliers_df)} rows")
print(f"Orders: {len(orders_df)} rows")