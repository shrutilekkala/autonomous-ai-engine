select
    snapshot_id,
    store_id,
    sku_id,
    cast(snapshot_date as date) as snapshot_date,
    snapshot_time,
    units_on_hand,
    units_in_backroom,
    days_of_supply,
    cast(expiry_nearest_date as date) as expiry_nearest_date
from {{ source('raw', 'raw_inventory_snapshots') }}