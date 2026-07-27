select
    promotion_id,
    promotion_name,
    promo_type,
    cast(start_date as date) as start_date,
    cast(end_date as date) as end_date,
    discount_pct,
    sku_id,
    store_id,
    demand_lift_factor
from {{ source('raw', 'raw_promotions') }}