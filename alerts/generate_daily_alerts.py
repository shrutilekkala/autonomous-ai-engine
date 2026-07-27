import duckdb
import pandas as pd
from datetime import datetime
import os

con = duckdb.connect("../warehouse.duckdb")
RUN_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
os.makedirs("alert_logs", exist_ok=True)

alerts = []

# ── TIER 1: Stockout risk (classifier + timing feature) ────────────────
# Only the LATEST snapshot per store-SKU — mimics a real daily check, not
# a historical audit of every day this was ever true.
print("Checking stockout risk...")
risk = con.execute("""
    WITH latest_per_sku AS (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY store_id, sku_id ORDER BY snapshot_date DESC
            ) AS rn
        FROM feat_inventory_risk
    )
    SELECT store_id, sku_id, category, days_of_supply,
           insufficient_supply_for_leadtime, below_reorder_point
    FROM latest_per_sku
    WHERE rn = 1
      AND is_stocked_out = false
      AND insufficient_supply_for_leadtime = true
""").fetchdf()

for row in risk.itertuples():
    severity = "critical" if row.below_reorder_point else "high"
    alerts.append({
        "alert_type": "stockout_risk",
        "severity": severity,
        "store_id": row.store_id,
        "sku_id": row.sku_id,
        "category": row.category,
        "message": f"{row.sku_id} at {row.store_id}: only {round(row.days_of_supply,1)} days "
                   f"of supply left, below the supplier's typical lead time. Reorder now.",
        "run_date": RUN_DATE,
    })
print(f"  {len(risk):,} stockout-risk alerts")

# ── TIER 2: Anomalies (sales + inventory) — last 7 days of data only ───
print("Checking anomalies...")
sales_anom = con.execute("""
    SELECT store_id, sku_id, sale_date, anomaly_type, z_score
    FROM anomaly_sales
    WHERE is_anomaly = true
      AND sale_date >= (SELECT MAX(sale_date) - INTERVAL 7 DAY FROM anomaly_sales)
    ORDER BY sale_date DESC
    LIMIT 50
""").fetchdf()

for row in sales_anom.itertuples():
    alerts.append({
        "alert_type": "sales_anomaly",
        "severity": "watch",
        "store_id": row.store_id,
        "sku_id": row.sku_id,
        "category": None,
        "message": f"{row.sku_id} at {row.store_id} on {row.sale_date}: unusual sales "
                   f"{row.anomaly_type} (z-score {round(row.z_score,1)}).",
        "run_date": RUN_DATE,
    })

inv_anom = con.execute("""
    SELECT store_id, sku_id, snapshot_date, day_over_day_change, z_score
    FROM anomaly_inventory
    WHERE is_anomaly = true
      AND snapshot_date >= (SELECT MAX(snapshot_date) - INTERVAL 7 DAY FROM anomaly_inventory)
    ORDER BY snapshot_date DESC
    LIMIT 50
""").fetchdf()

for row in inv_anom.itertuples():
    direction = "drop" if row.day_over_day_change < 0 else "spike"
    alerts.append({
        "alert_type": "inventory_anomaly",
        "severity": "watch",
        "store_id": row.store_id,
        "sku_id": row.sku_id,
        "category": None,
        "message": f"{row.sku_id} at {row.store_id} on {row.snapshot_date}: unexplained "
                   f"inventory {direction} of {abs(int(row.day_over_day_change))} units.",
        "run_date": RUN_DATE,
    })
print(f"  {len(sales_anom)+len(inv_anom):,} anomaly alerts (last 7 days of data, capped at 50 each)")

# ── TIER 3: Shelf space — top 3 per store, per type ─────────────────────
print("Checking shelf space recommendations...")
removals = con.execute("""
    SELECT store_id, sku_id, aisle_name, capacity_units, evidence_chainwide_units
    FROM mart_shelf_swap_recommendations
    WHERE recommendation_type = 'removal_candidate'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY store_id ORDER BY capacity_units DESC) <= 3
""").fetchdf()

for row in removals.itertuples():
    alerts.append({
        "alert_type": "shelf_removal_candidate",
        "severity": "low",
        "store_id": row.store_id,
        "sku_id": row.sku_id,
        "category": None,
        "message": f"{row.sku_id} at {row.store_id} ({row.aisle_name}): occupies "
                   f"{row.capacity_units} capacity units but hasn't sold here, despite "
                   f"selling {int(row.evidence_chainwide_units):,} units chainwide. "
                   f"Consider reallocating this space.",
        "run_date": RUN_DATE,
    })

expansions = con.execute("""
    SELECT store_id, sku_id, aisle_name, capacity_units, sales_per_capacity_unit
    FROM mart_shelf_swap_recommendations
    WHERE recommendation_type = 'expansion_candidate'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY store_id ORDER BY sales_per_capacity_unit DESC) <= 3
""").fetchdf()

for row in expansions.itertuples():
    alerts.append({
        "alert_type": "shelf_expansion_candidate",
        "severity": "medium",
        "store_id": row.store_id,
        "sku_id": row.sku_id,
        "category": None,
        "message": f"{row.sku_id} at {row.store_id} ({row.aisle_name}): high sales velocity "
                   f"relative to its {row.capacity_units}-unit space "
                   f"({round(row.sales_per_capacity_unit,2)} units sold per capacity unit). "
                   f"Consider expanding its shelf allocation.",
        "run_date": RUN_DATE,
    })
print(f"  {len(removals)+len(expansions):,} shelf-space alerts (top 3 per store, per type)")

# ── Save results ─────────────────────────────────────────────────────
alerts_df = pd.DataFrame(alerts)
severity_order = {"critical": 0, "high": 1, "medium": 2, "watch": 3, "low": 4}
alerts_df["severity_rank"] = alerts_df["severity"].map(severity_order)
alerts_df = alerts_df.sort_values(["severity_rank", "store_id"]).drop(columns="severity_rank")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
alerts_df.to_csv(f"alert_logs/alerts_{timestamp}.csv", index=False)

print("\n" + "="*60)
print("ALERT SUMMARY")
print("="*60)
print(alerts_df["severity"].value_counts())
print(f"\nTotal alerts generated: {len(alerts_df):,}")
print(f"Saved to alert_logs/alerts_{timestamp}.csv")

print("\n--- Sample: top 5 critical alerts ---")
critical = alerts_df[alerts_df["severity"] == "critical"].head(5)
for row in critical.itertuples():
    print(f"  [{row.severity.upper()}] {row.message}")

con.close()