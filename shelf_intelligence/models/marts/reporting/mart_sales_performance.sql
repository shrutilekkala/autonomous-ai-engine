{{ config(materialized='table') }}
select
    st.region,
    p.category,
    date_trunc('month', f.sale_date) as sale_month,
    sum(f.units_sold) as total_units_sold,
    sum(f.revenue) as total_revenue,
    sum(f.gross_margin) as total_gross_margin,
    sum(case when f.is_promoted then f.revenue else 0 end) as promo_revenue,
    count(distinct f.sku_id) as distinct_skus_sold
from {{ ref('fact_sales') }} f
left join {{ ref('dim_stores') }} st on f.store_id = st.store_id
left join {{ ref('dim_products') }} p on f.sku_id = p.sku_id
group by st.region, p.category, date_trunc('month', f.sale_date)