import duckdb
import time

con = duckdb.connect("../warehouse.duckdb")

print("Building training dataset (this may take 1-3 minutes)...")
start = time.time()

query = """
SELECT
    i.store_id,
    i.sku_id,
    i.snapshot_date,
    i.units_on_hand,
    i.units_in_backroom,
    i.days_of_supply,
    i.reorder_point,
    i.safety_stock,
    i.below_reorder_point,
    i.insufficient_supply_for_leadtime,
    i.low_reliability_supplier,
    i.is_perishable,
    i.category,
    i.reliability_score,
    i.lead_time_days_avg,
    CASE WHEN EXISTS (
        SELECT 1 FROM fact_stockouts s
        WHERE s.store_id = i.store_id
          AND s.sku_id = i.sku_id
          AND s.stockout_date > i.snapshot_date
          AND s.stockout_date <= i.snapshot_date + INTERVAL 14 DAY
    ) THEN 1 ELSE 0 END AS stockout_within_14d
FROM feat_inventory_risk i
WHERE i.is_stocked_out = false
"""

df = con.execute(query).fetchdf()
elapsed = round(time.time() - start, 1)

print(f"\nDone in {elapsed}s")
print(f"Total rows: {len(df):,}")
print(f"\nClass balance:")
print(df['stockout_within_14d'].value_counts())
print(f"\nPositive class (will stock out): {round(100*df['stockout_within_14d'].mean(),2)}%")

df.to_parquet("training_data.parquet")
print("\nSaved to ml/training_data.parquet")

con.close()