{{ config(materialized='table') }}

select
    inv.store_id,
    inv.sku_id,
    inv.snapshot_date,
    inv.units_on_hand,
    inv.units_in_backroom,
    inv.days_of_supply,
    inv.below_reorder_point,
    inv.is_stocked_out,
    inv.is_phantom_inventory,

    p.reorder_point,
    p.safety_stock,
    p.is_perishable,
    p.category,

    sup.reliability_score,
    sup.lead_time_days_avg,

    -- risk flags
    (inv.days_of_supply < sup.lead_time_days_avg) as insufficient_supply_for_leadtime,
    (sup.reliability_score < 0.85) as low_reliability_supplier

from {{ ref('fact_inventory') }} inv
left join {{ ref('dim_products') }} p on inv.sku_id = p.sku_id
left join {{ ref('dim_suppliers') }} sup on p.supplier_id = sup.supplier_id