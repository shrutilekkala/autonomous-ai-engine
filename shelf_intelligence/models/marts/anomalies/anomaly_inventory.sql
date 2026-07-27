{{ config(materialized='table') }}

with daily_change as (
    select
        store_id,
        sku_id,
        snapshot_date,
        units_on_hand,
        lag(units_on_hand) over (
            partition by store_id, sku_id order by snapshot_date
        ) as prev_units_on_hand,
        units_on_hand - lag(units_on_hand) over (
            partition by store_id, sku_id order by snapshot_date
        ) as day_over_day_change,
        row_number() over (
            partition by store_id, sku_id order by snapshot_date
        ) as day_number
    from {{ ref('fact_inventory') }}
),
rolling_change_stats as (
    select
        *,
        avg(day_over_day_change) over (
            partition by store_id, sku_id order by snapshot_date
            rows between 30 preceding and 1 preceding
        ) as rolling_mean_change,
        stddev(day_over_day_change) over (
            partition by store_id, sku_id order by snapshot_date
            rows between 30 preceding and 1 preceding
        ) as rolling_std_change
    from daily_change
)
select
    store_id,
    sku_id,
    snapshot_date,
    units_on_hand,
    prev_units_on_hand,
    day_over_day_change,
    case
        when rolling_std_change is null or rolling_std_change = 0 then null
        else (day_over_day_change - rolling_mean_change) / rolling_std_change
    end as z_score,
    case
        when rolling_std_change is null or rolling_std_change = 0 then false
        else abs((day_over_day_change - rolling_mean_change) / rolling_std_change) > 3
    end as is_anomaly
from rolling_change_stats
where rolling_mean_change is not null
  and day_number > 30