{{ config(materialized='table') }}
select
    inv.snapshot_id,
    inv.store_id,
    inv.sku_id,
    inv.snapshot_date,
    inv.units_on_hand,
    inv.units_in_backroom,
    inv.days_of_supply,
    inv.expiry_nearest_date,
    (inv.units_on_hand <= p.reorder_point) as below_reorder_point,
    (inv.units_on_hand = 0) as is_stocked_out,
    (inv.units_in_backroom > 0 and inv.units_on_hand = 0) as is_phantom_inventory
from {{ ref('stg_inventory_snapshots') }} inv
left join {{ ref('stg_products') }} p on inv.sku_id = p.sku_id