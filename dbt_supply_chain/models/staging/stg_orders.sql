SELECT
    order_id,
    product_id,
    supplier_id,
    order_date,
    delivery_date,
    promised_date,
    quantity_ordered,
    quantity_received,
    unit_price,
    product_category,
    region,
    DATEDIFF('day', promised_date, delivery_date) AS delay_days,
    CASE WHEN delivery_date <= promised_date THEN 1 ELSE 0 END AS on_time_flag
FROM SUPPLY_CHAIN_DB.STAGING.STG_ORDERS