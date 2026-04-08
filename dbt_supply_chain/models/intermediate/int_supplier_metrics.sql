SELECT
    s.supplier_id,
    s.supplier_name,
    s.location_zone,
    s.payment_terms,
    s.otd_rate,
    s.lead_time_avg,
    s.lead_time_variance,
    s.defect_rate,
    s.order_volume,
    COUNT(o.order_id)                        AS total_orders,
    AVG(o.delay_days)                        AS avg_delay_days,
    SUM(o.on_time_flag)                      AS on_time_deliveries,
    ROUND(AVG(o.quantity_received / NULLIF(o.quantity_ordered, 0)) * 100, 2) AS fill_rate_pct
FROM {{ ref('stg_suppliers') }} s
LEFT JOIN {{ ref('stg_orders') }} o ON s.supplier_id = o.supplier_id
GROUP BY ALL