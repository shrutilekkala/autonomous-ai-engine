{{ config(materialized='table') }}
select
    st.region,
    st.store_format,
    p.category,
    f.root_cause,
    count(*) as stockout_events,
    sum(f.estimated_lost_units) as total_lost_units,
    sum(f.estimated_lost_revenue) as total_lost_revenue,
    avg(f.duration_days) as avg_duration_days,
    avg(sup.reliability_score) as avg_supplier_reliability,
    avg(sup.lead_time_days_avg) as avg_supplier_lead_time
from {{ ref('fact_stockouts') }} f
left join {{ ref('dim_stores') }} st on f.store_id = st.store_id
left join {{ ref('dim_products') }} p on f.sku_id = p.sku_id
left join {{ ref('dim_suppliers') }} sup on p.supplier_id = sup.supplier_id
group by st.region, st.store_format, p.category, f.root_cause