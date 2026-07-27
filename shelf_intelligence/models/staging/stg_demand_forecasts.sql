select
    forecast_id,
    store_id,
    sku_id,
    cast(forecast_date as date) as forecast_date,
    forecast_units,
    forecast_method,
    cast(created_at as date) as created_at,
    lower_bound_90,
    upper_bound_90
from {{ source('raw', 'raw_demand_forecasts') }}