SELECT
    supplier_id,
    supplier_name,
    location_zone,
    payment_terms,
    otd_rate,
    lead_time_avg,
    lead_time_variance,
    defect_rate,
    order_volume
FROM SUPPLY_CHAIN_DB.STAGING.STG_SUPPLIERS