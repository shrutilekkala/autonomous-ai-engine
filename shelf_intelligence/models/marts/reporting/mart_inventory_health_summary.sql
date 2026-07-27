{{ config(materialized='table') }}
select
    st.region,
    p.category,
    p.is_perishable,
    count(*) as snapshot_count,
    avg(f.days_of_supply) as avg_days_of_supply,
    sum(case when f.below_reorder_point then 1 else 0 end) as below_reorder_count,
    sum(case when f.is_stocked_out then 1 else 0 end) as stocked_out_count,
    sum(case when f.is_phantom_inventory then 1 else 0 end) as phantom_inventory_count,
    round(100.0 * sum(case when f.is_phantom_inventory then 1 else 0 end) / count(*), 2) as phantom_inventory_pct
from {{ ref('fact_inventory') }} f
left join {{ ref('dim_stores') }} st on f.store_id = st.store_id
left join {{ ref('dim_products') }} p on f.sku_id = p.sku_id
group by st.region, p.category, p.is_perishable