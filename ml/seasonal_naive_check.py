import duckdb
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

con = duckdb.connect("../warehouse.duckdb")

print("Computing SeasonalNaive (same day, last year) baseline...")

df = con.execute("""
    SELECT
        curr.store_id, curr.sku_id, curr.sale_date,
        curr.daily_units_sold AS actual,
        prev.daily_units_sold AS seasonal_naive_pred
    FROM feat_sales_daily curr
    JOIN feat_sales_daily prev
      ON curr.store_id = prev.store_id
     AND curr.sku_id = prev.sku_id
     AND prev.sale_date = curr.sale_date - INTERVAL 364 DAY  -- nearest same weekday, 52 weeks back
    WHERE curr.sale_date >= '2025-08-04'
""").fetchdf()

print(f"Matched rows: {len(df):,}")

if len(df) == 0:
    print("No matches — insufficient history for a full year-over-year comparison.")
else:
    mae = mean_absolute_error(df["actual"], df["seasonal_naive_pred"])
    mape = mean_absolute_percentage_error(
        df["actual"].clip(lower=1), df["seasonal_naive_pred"].clip(lower=1)
    ) * 100
    print(f"\nSeasonalNaive (this day, last year):")
    print(f"  MAE:  {round(mae,3)}")
    print(f"  MAPE: {round(mape,2)}%")
    print(f"\nCompare to LightGBM: MAE=2.685, MAPE=40.95%")
    print(f"Compare to best rolling-avg naive: MAE=3.016, MAPE=42.56%")

con.close()