SELECT
    supplier_id,
    supplier_name,
    location_zone,
    payment_terms,
    otd_rate,
    lead_time_variance,
    defect_rate,
    order_volume,
    total_orders,
    avg_delay_days,
    fill_rate_pct,
    CASE
        WHEN otd_rate < 0.65 AND lead_time_variance > 7 THEN 'Critical Watch'
        WHEN otd_rate < 0.75 AND lead_time_variance > 5 THEN 'Delivery Risk'
        WHEN defect_rate > 0.12 THEN 'Cost Risk'
        ELSE 'Reliable Partner'
    END AS risk_label
FROM {{ ref('int_supplier_metrics') }}