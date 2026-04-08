import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import snowflake.connector
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="Supply Chain Intelligence", layout="wide")

@st.cache_data
def load_data():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account="gsxalxt-hp10837",
        warehouse="COMPUTE_WH",
        database="SUPPLY_CHAIN_DB",
        schema="ANALYTICS"
    )
    ml_df = pd.read_sql("SELECT * FROM MART_ML_OUTPUTS", conn)
    orders_df = pd.read_sql("SELECT * FROM STG_ORDERS", conn)
    conn.close()
    ml_df.columns = ml_df.columns.str.lower()
    orders_df.columns = orders_df.columns.str.lower()
    return ml_df, orders_df

ml_df, orders_df = load_data()

st.title("🏭 Smart Supplier Risk & Demand Intelligence Platform")
st.markdown("---")

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

    # Simple forecast: last 3 months rolling average as next month
    last_3_avg = monthly['Actual Demand'].tail(3).mean()
    forecast_row = pd.DataFrame({'Month': ['Forecast (Next)'], 'Actual Demand': [None], 'Forecast': [last_3_avg]})
    monthly['Forecast'] = None

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(monthly['Month'], monthly['Actual Demand'], marker='o', label='Actual', color='steelblue')
    ax.axhline(last_3_avg, color='orange', linestyle='--', label=f'30-Day Forecast: {last_3_avg:.0f} units')
    ax.set_xlabel('Month')
    ax.set_ylabel('Quantity Ordered')
    ax.set_title(f'Demand Trend — {category}')
    plt.xticks(rotation=45)
    ax.legend()
    st.pyplot(fig)

    col1, col2 = st.columns(2)
    col1.metric("Forecasted Demand (Next 30 days)", f"{last_3_avg:,.0f} units")
    col2.metric("Model MAPE", "29.15%", delta="Simulated Data")

# ── TAB 2: Supplier Risk Map ──
with tab2:
    st.subheader("Supplier Risk Segmentation")

    col1, col2 = st.columns([1, 2])
    with col1:
        risk_filter = st.multiselect(
            "Filter by Risk Level",
            options=['High', 'Medium', 'Low'],
            default=['High', 'Medium', 'Low']
        )
        zone_filter = st.multiselect(
            "Filter by Zone",
            options=ml_df['location_zone'].unique().tolist(),
            default=ml_df['location_zone'].unique().tolist()
        )

    filtered_df = ml_df[
        (ml_df['predicted_risk'].isin(risk_filter)) &
        (ml_df['location_zone'].isin(zone_filter))
    ]

    def color_risk(val):
        colors = {'High': 'background-color: #ff4b4b; color: white',
                  'Medium': 'background-color: #ffa500; color: white',
                  'Low': 'background-color: #21c354; color: white'}
        return colors.get(val, '')

    display_df = filtered_df[[
        'supplier_id', 'supplier_name', 'location_zone',
        'cluster_label', 'predicted_risk', 'risk_score',
        'otd_rate', 'lead_time_variance', 'defect_rate'
    ]].sort_values('risk_score', ascending=False)

    st.dataframe(
        display_df.style.applymap(color_risk, subset=['predicted_risk']),
        use_container_width=True, height=400
    )

    st.markdown("**Cluster Distribution**")
    cluster_counts = ml_df['cluster_label'].value_counts()
    fig2, ax2 = plt.subplots(figsize=(6, 3))
    colors = ['#ff4b4b', '#ffa500', '#21c354', '#1f77b4']
    ax2.bar(cluster_counts.index, cluster_counts.values, color=colors)
    ax2.set_ylabel('Supplier Count')
    st.pyplot(fig2)

# ── TAB 3: Alert Panel ──
with tab3:
    st.subheader("🚨 Top High-Risk Suppliers — Immediate Action Required")

    high_risk = ml_df[ml_df['predicted_risk'] == 'High'].sort_values('risk_score', ascending=False).head(10)

    for _, row in high_risk.iterrows():
        with st.expander(f"⚠️ {row['supplier_name']} ({row['supplier_id']}) — Zone: {row['location_zone']}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("OTD Rate", f"{row['otd_rate']*100:.1f}%")
            col2.metric("Lead Time Variance", f"{row['lead_time_variance']:.1f} days")
            col3.metric("Defect Rate", f"{row['defect_rate']*100:.1f}%")
            st.markdown(f"**Cluster:** `{row['cluster_label']}` | **Risk Score:** `{row['risk_score']:.4f}`")
            reason = []
            if row['otd_rate'] < 0.70: reason.append("Low OTD rate")
            if row['lead_time_variance'] > 6: reason.append("High lead time variance")
            if row['defect_rate'] > 0.12: reason.append("High defect rate")
            st.error(f"**Reason Codes:** {', '.join(reason) if reason else 'Multiple risk factors'}")

    st.markdown("---")
    st.markdown("**Risk Distribution by Zone**")
    zone_risk = ml_df.groupby(['location_zone', 'predicted_risk']).size().unstack(fill_value=0)
    st.bar_chart(zone_risk)