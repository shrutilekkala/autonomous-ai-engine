{{ config(materialized='table') }}
select
    st.region,
    p.category,
    sup.supplier_name,
    f.trigger_type,
    count(*) as order_count,
    sum(f.units_ordered) as total_units_ordered,
    sum(f.units_received) as total_units_received,
    round(100.0 * sum(f.units_received) / nullif(sum(f.units_ordered),0), 2) as fulfillment_rate_pct,
    avg(f.lead_time_variance) as avg_lead_time_variance,
    sum(f.replenishment_cost) as total_cost,
    sum(case when f.had_shortfall then 1 else 0 end) as shortfall_orders
from {{ ref('fact_replenishment') }} f
left join {{ ref('dim_stores') }} st on f.store_id = st.store_id
left join {{ ref('dim_products') }} p on f.sku_id = p.sku_id
left join {{ ref('dim_suppliers') }} sup on p.supplier_id = sup.supplier_id
group by st.region, p.category, sup.supplier_name, f.trigger_type