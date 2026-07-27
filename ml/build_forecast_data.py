import duckdb
import time

con = duckdb.connect("../warehouse.duckdb")

print("Aggregating to store-SKU-day level with lag features...")
t0 = time.time()

query = """
WITH base AS (
    SELECT
        store_id, sku_id, sale_date,
        daily_units_sold, month, day_of_week,
        is_weekend, is_december, is_holiday_season,
        region, foot_traffic_tier, category, is_perishable
    FROM feat_sales_daily
),
with_lags AS (
    SELECT *,
        LAG(daily_units_sold, 1) OVER (
            PARTITION BY store_id, sku_id ORDER BY sale_date
        ) AS units_lag_1d,
        LAG(daily_units_sold, 7) OVER (
            PARTITION BY store_id, sku_id ORDER BY sale_date
        ) AS units_lag_7d,
        AVG(daily_units_sold) OVER (
            PARTITION BY store_id, sku_id ORDER BY sale_date
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) AS units_rolling_avg_7d,
        AVG(daily_units_sold) OVER (
            PARTITION BY store_id, sku_id ORDER BY sale_date
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        ) AS units_rolling_avg_30d
    FROM base
)
SELECT * FROM with_lags
WHERE units_lag_7d IS NOT NULL
  AND units_rolling_avg_30d IS NOT NULL
"""

df = con.execute(query).fetchdf()
print(f"Done in {round(time.time()-t0,1)}s — {len(df):,} rows")
df.to_parquet("forecast_data.parquet")
print("Saved to ml/forecast_data.parquet")

con.close()