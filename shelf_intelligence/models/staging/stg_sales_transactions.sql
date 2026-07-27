select
    transaction_id,
    store_id,
    sku_id,
    cast(sale_date as date) as sale_date,
    units_sold,
    unit_price_actual,
    revenue,
    is_promoted,
    promotion_id
from {{ source('raw', 'raw_sales_transactions') }}