select
    store_id,
    store_name,
    region,
    city,
    state,
    store_format,
    foot_traffic_tier,
    num_aisles,
    cast(open_date as date) as open_date,
    sq_footage
from {{ source('raw', 'raw_stores') }}