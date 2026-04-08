import snowflake.connector
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account="gsxalxt-hp10837",
    warehouse="COMPUTE_WH",
    database="SUPPLY_CHAIN_DB",
    schema="STAGING"
)

cursor = conn.cursor()

def load_df_to_snowflake(df, table_name):
    cols = ', '.join(df.columns)
    placeholders = ', '.join(['%s'] * len(df.columns))
    insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
    data = [tuple(row) for row in df.itertuples(index=False)]
    cursor.executemany(insert_sql, data)
    print(f"Loaded {len(data)} rows into {table_name}")

# Load suppliers
suppliers_df = pd.read_csv('data/raw/suppliers.csv')
load_df_to_snowflake(suppliers_df, 'STG_SUPPLIERS')

# Load orders
orders_df = pd.read_csv('data/raw/orders.csv')
orders_df['order_date'] = pd.to_datetime(orders_df['order_date']).dt.strftime('%Y-%m-%d')
orders_df['delivery_date'] = pd.to_datetime(orders_df['delivery_date']).dt.strftime('%Y-%m-%d')
orders_df['promised_date'] = pd.to_datetime(orders_df['promised_date']).dt.strftime('%Y-%m-%d')
load_df_to_snowflake(orders_df, 'STG_ORDERS')

conn.commit()
cursor.close()
conn.close()
print("All data loaded successfully!")