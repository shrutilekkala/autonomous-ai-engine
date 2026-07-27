select
    stockout_id,
    store_id,
    sku_id,
    cast(stockout_date as date) as stockout_date,
    cast(restock_date as date) as restock_date,
    duration_days,
    estimated_lost_units,
    estimated_lost_revenue,
    root_cause,
    (restock_date is null) as is_ongoing
from {{ source('raw', 'raw_stockout_events') }}