{{ config(materialized='table') }}

with rolling_stats as (
    select
        store_id,
        sku_id,
        sale_date,
        daily_units_sold,
        row_number() over (
            partition by store_id, sku_id order by sale_date
        ) as day_number,
        avg(daily_units_sold) over (
            partition by store_id, sku_id order by sale_date
            rows between 30 preceding and 1 preceding
        ) as rolling_mean_30d,
        stddev(daily_units_sold) over (
            partition by store_id, sku_id order by sale_date
            rows between 30 preceding and 1 preceding
        ) as rolling_std_30d
    from {{ ref('feat_sales_daily') }}
)
select
    store_id,
    sku_id,
    sale_date,
    daily_units_sold,
    rolling_mean_30d,
    rolling_std_30d,
    case
        when rolling_std_30d is null or rolling_std_30d = 0 then null
        else (daily_units_sold - rolling_mean_30d) / rolling_std_30d
    end as z_score,
    case
        when rolling_std_30d is null or rolling_std_30d = 0 then false
        else abs((daily_units_sold - rolling_mean_30d) / rolling_std_30d) > 3
    end as is_anomaly,
    case
        when rolling_std_30d is not null and rolling_std_30d > 0
             and (daily_units_sold - rolling_mean_30d) / rolling_std_30d > 3
        then 'spike'
        when rolling_std_30d is not null and rolling_std_30d > 0
             and (daily_units_sold - rolling_mean_30d) / rolling_std_30d < -3
        then 'drop'
        else null
    end as anomaly_type
from rolling_stats
where rolling_mean_30d is not null
  and day_number > 30