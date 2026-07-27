{{ config(materialized='table') }}

with sku_global_sales as (
    -- does this SKU sell meaningfully anywhere in the chain? proves it's a real, viable product
    select sku_id, sum(units_sold) as total_units_chainwide
    from {{ ref('fact_sales') }}
    group by sku_id
),
removal_candidates as (
    select
        fe.store_id,
        fe.sku_id,
        fe.aisle_name,
        fe.shelf_id,
        fe.slot_id,
        fe.capacity_units,
        fe.facing_count,
        fe.category,
        g.total_units_chainwide,
        'removal_candidate' as recommendation_type
    from {{ ref('feat_shelf_efficiency') }} fe
    join sku_global_sales g on fe.sku_id = g.sku_id
    where fe.shelf_status = 'dead_stock'
      and g.total_units_chainwide > 1000   -- proven viable product elsewhere, just misplaced here
),
expansion_candidates as (
    select
        fe.store_id,
        fe.sku_id,
        fe.aisle_name,
        fe.shelf_id,
        fe.slot_id,
        fe.capacity_units,
        fe.facing_count,
        fe.category,
        fe.avg_daily_units_sold,
        fe.sales_per_capacity_unit,
        'expansion_candidate' as recommendation_type
    from {{ ref('feat_shelf_efficiency') }} fe
    where fe.shelf_status = 'high_velocity_undersized'
)
select
    store_id, sku_id, aisle_name, shelf_id, slot_id,
    capacity_units, facing_count, category,
    recommendation_type,
    total_units_chainwide as evidence_chainwide_units,
    null as avg_daily_units_sold,
    null as sales_per_capacity_unit
from removal_candidates

union all

select
    store_id, sku_id, aisle_name, shelf_id, slot_id,
    capacity_units, facing_count, category,
    recommendation_type,
    null as evidence_chainwide_units,
    avg_daily_units_sold,
    sales_per_capacity_unit
from expansion_candidates