{{ config(materialized='table') }}

select
    f.store_id,
    f.sku_id,
    f.sale_date,
    sum(f.units_sold) as daily_units_sold,
    sum(f.revenue) as daily_revenue,
    avg(f.unit_price_actual) as avg_price,
    max(case when f.is_promoted then 1 else 0 end) as was_promoted,

    -- time-based features, directly justified by EDA findings
    extract(month from f.sale_date) as month,
    extract(dow from f.sale_date) as day_of_week,       -- 0=Sunday in DuckDB
    (extract(dow from f.sale_date) in (5,6)) as is_weekend,
    (extract(month from f.sale_date) = 12) as is_december,
    (extract(month from f.sale_date) in (11,12)) as is_holiday_season,

    -- store context
    st.region,
    st.foot_traffic_tier,
    st.store_format,

    -- product context
    p.category,
    p.subcategory,
    p.is_perishable

from {{ ref('fact_sales') }} f
left join {{ ref('dim_stores') }} st on f.store_id = st.store_id
left join {{ ref('dim_products') }} p on f.sku_id = p.sku_id
group by
    f.store_id, f.sku_id, f.sale_date,
    st.region, st.foot_traffic_tier, st.store_format,
    p.category, p.subcategory, p.is_perishable