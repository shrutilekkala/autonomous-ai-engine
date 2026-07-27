{{ config(materialized='table') }}
select
    rl.replenishment_id,
    rl.store_id,
    rl.sku_id,
    rl.replenishment_date,
    rl.trigger_type,
    rl.units_ordered,
    rl.units_received,
    rl.had_shortfall,
    rl.replenishment_cost,
    rl.lead_time_actual,
    (rl.lead_time_actual - sup.lead_time_days_avg) as lead_time_variance
from {{ ref('stg_replenishment_logs') }} rl
left join {{ ref('stg_products') }} p on rl.sku_id = p.sku_id
left join {{ ref('stg_suppliers') }} sup on p.supplier_id = sup.supplier_id