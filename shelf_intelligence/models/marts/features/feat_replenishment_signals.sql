{{ config(materialized='table') }}

select
    r.store_id,
    r.sku_id,

    count(*) as replenishment_count,
    avg(r.lead_time_actual) as avg_lead_time_actual,
    avg(r.lead_time_variance) as avg_lead_time_variance,
    stddev(r.lead_time_actual) as lead_time_volatility,

    -- replaced the useless binary flag with actual shortfall magnitude
    avg(r.units_ordered - r.units_received) as avg_shortfall_units,
    avg(100.0 * (r.units_ordered - r.units_received) / nullif(r.units_ordered,0)) as avg_shortfall_pct,
    stddev(100.0 * (r.units_ordered - r.units_received) / nullif(r.units_ordered,0)) as shortfall_volatility,

    sum(case when r.trigger_type = 'Emergency' then 1 else 0 end) as emergency_order_count,
    avg(r.replenishment_cost) as avg_replenishment_cost,

    max(r.replenishment_date) as last_replenishment_date

from {{ ref('fact_replenishment') }} r
group by r.store_id, r.sku_id