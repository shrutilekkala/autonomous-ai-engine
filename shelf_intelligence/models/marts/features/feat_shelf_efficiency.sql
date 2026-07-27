{{ config(materialized='table') }}

with sales_velocity as (
    select
        store_id,
        sku_id,
        avg(daily_units_sold) as avg_daily_units_sold
    from {{ ref('feat_sales_daily') }}
    group by store_id, sku_id
),
layout as (
    select
        store_id,
        assigned_sku_id as sku_id,
        aisle_id,
        aisle_name,
        shelf_id,
        slot_id,
        capacity_units,
        facing_count
    from {{ ref('stg_store_layout') }}
    where assigned_sku_id is not null
)
select
    l.store_id,
    l.sku_id,
    l.aisle_name,
    l.shelf_id,
    l.slot_id,
    l.capacity_units,
    l.facing_count,
    coalesce(sv.avg_daily_units_sold, 0) as avg_daily_units_sold,

    -- units sold per unit of shelf capacity — the core efficiency metric
    round(coalesce(sv.avg_daily_units_sold, 0) / nullif(l.capacity_units, 0), 4) as sales_per_capacity_unit,

    -- units sold per facing — is each facing "earning its keep"
    round(coalesce(sv.avg_daily_units_sold, 0) / nullif(l.facing_count, 0), 4) as sales_per_facing,

    p.category,
    p.is_perishable,

    case
        when coalesce(sv.avg_daily_units_sold, 0) = 0 then 'dead_stock'
        when coalesce(sv.avg_daily_units_sold, 0) / nullif(l.capacity_units, 0) < 0.05 then 'underperforming'
        when coalesce(sv.avg_daily_units_sold, 0) / nullif(l.capacity_units, 0) > 0.5 then 'high_velocity_undersized'
        else 'balanced'
    end as shelf_status

from layout l
left join sales_velocity sv on l.store_id = sv.store_id and l.sku_id = sv.sku_id
left join {{ ref('dim_products') }} p on l.sku_id = p.sku_id