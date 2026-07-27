{{ config(materialized='table') }}
select
    stockout_id,
    store_id,
    sku_id,
    stockout_date,
    restock_date,
    duration_days,
    estimated_lost_units,
    estimated_lost_revenue,
    root_cause,
    is_ongoing
from {{ ref('stg_stockout_events') }}