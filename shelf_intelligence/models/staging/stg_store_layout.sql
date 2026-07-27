select
    layout_id,
    store_id,
    aisle_id,
    aisle_name,
    shelf_id,
    slot_id,
    capacity_units,
    assigned_sku_id,
    facing_count
from {{ source('raw', 'raw_store_layout') }}