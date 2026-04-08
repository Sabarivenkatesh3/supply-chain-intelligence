import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import snowflake.connector

st.set_page_config(page_title="Supply Chain Intelligence", layout="wide")

# ✅ Load data from Snowflake using Streamlit secrets
@st.cache_data
def load_data():
    try:
        conn = snowflake.connector.connect(
            user=st.secrets["SNOWFLAKE_USER"],
            password=st.secrets["SNOWFLAKE_PASSWORD"],
            account=st.secrets["SNOWFLAKE_ACCOUNT"],
            warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
            database=st.secrets["SNOWFLAKE_DATABASE"],
            schema=st.secrets["SNOWFLAKE_SCHEMA"]
        )

        ml_df = pd.read_sql("SELECT * FROM MART_ML_OUTPUTS", conn)
        orders_df = pd.read_sql("SELECT * FROM STG_ORDERS", conn)

        conn.close()

        ml_df.columns = ml_df.columns.str.lower()
        orders_df.columns = orders_df.columns.str.lower()

        return ml_df, orders_df

    except Exception as e:
        st.error(f"❌ Snowflake connection failed: {e}")
        return pd.DataFrame(), pd.DataFrame()


ml_df, orders_df = load_data()

st.title("🏭 Smart Supplier Risk & Demand Intelligence Platform")
st.markdown("---")

# Stop app if data not loaded
if ml_df.empty or orders_df.empty:
    st.warning("⚠️ Data not loaded. Please check Snowflake credentials.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📈 Demand Forecast", "🏷️ Supplier Risk Map", "🚨 Alert Panel"])

# ── TAB 1: Demand Forecast ──
with tab1:
    st.subheader("30-Day Demand Forecast by Product Category")

    orders_df['order_date'] = pd.to_datetime(orders_df['order_date'])
    orders_df['month'] = orders_df['order_date'].dt.to_period('M').astype(str)

    category = st.selectbox("Select Product Category", orders_df['product_category'].unique())
    filtered = orders_df[orders_df['product_category'] == category]
    monthly = filtered.groupby('month')['quantity_ordered'].sum().reset_index()
    monthly.columns = ['Month', 'Actual Demand']
    monthly = monthly.sort_values('Month')

    last_3_avg = monthly['Actual Demand'].tail(3).mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(monthly['Month'], monthly['Actual Demand'], marker='o', label='Actual')
    ax.axhline(last_3_avg, linestyle='--', label=f'Forecast: {last_3_avg:.0f}')
    ax.set_xlabel('Month')
    ax.set_ylabel('Quantity Ordered')
    ax.legend()
    plt.xticks(rotation=45)

    st.pyplot(fig)

    col1, col2 = st.columns(2)
    col1.metric("Forecasted Demand", f"{last_3_avg:,.0f} units")
    col2.metric("Model MAPE", "29.15%")

# ── TAB 2: Supplier Risk Map ──
with tab2:
    st.subheader("Supplier Risk Segmentation")

    risk_filter = st.multiselect(
        "Risk Level",
        ['High', 'Medium', 'Low'],
        default=['High', 'Medium', 'Low']
    )

    zone_filter = st.multiselect(
        "Zone",
        ml_df['location_zone'].unique(),
        default=ml_df['location_zone'].unique()
    )

    filtered_df = ml_df[
        (ml_df['predicted_risk'].isin(risk_filter)) &
        (ml_df['location_zone'].isin(zone_filter))
    ]

    st.dataframe(filtered_df, use_container_width=True)

# ── TAB 3: Alerts ──
with tab3:
    st.subheader("🚨 High Risk Suppliers")

    high_risk = ml_df[ml_df['predicted_risk'] == 'High']

    st.dataframe(high_risk.head(10), use_container_width=True)

    st.bar_chart(
        ml_df.groupby(['location_zone', 'predicted_risk'])
        .size()
        .unstack(fill_value=0)
    )