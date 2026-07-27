{{ config(materialized='table') }}
select
    tx.transaction_id,
    tx.store_id,
    tx.sku_id,
    tx.sale_date,
    tx.units_sold,
    tx.unit_price_actual,
    tx.revenue,
    (tx.unit_price_actual - p.unit_cost) * tx.units_sold as gross_margin,
    tx.is_promoted,
    tx.promotion_id
from {{ ref('stg_sales_transactions') }} tx
left join {{ ref('stg_products') }} p on tx.sku_id = p.sku_id