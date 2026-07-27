select
    replenishment_id,
    store_id,
    sku_id,
    cast(replenishment_date as date) as replenishment_date,
    trigger_type,
    units_ordered,
    units_received,
    cast(order_date as date) as order_date,
    cast(receive_date as date) as receive_date,
    lead_time_actual,
    replenishment_cost,
    associate_id,
    (units_received < units_ordered) as had_shortfall
from {{ source('raw', 'raw_replenishment_logs') }}