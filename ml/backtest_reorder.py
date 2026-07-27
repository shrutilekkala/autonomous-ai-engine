import duckdb
import pandas as pd
import joblib

con = duckdb.connect("../warehouse.duckdb")
rf = joblib.load("model_rf_baseline.pkl")

features = [
    "units_on_hand", "units_in_backroom", "days_of_supply",
    "reorder_point", "safety_stock", "below_reorder_point",
    "insufficient_supply_for_leadtime", "low_reliability_supplier",
    "is_perishable", "category", "reliability_score", "lead_time_days_avg",
]

# ── Score every inventory snapshot in the test period with the classifier ──
print("Scoring inventory snapshots with the trained classifier...")
inv = con.execute("""
    SELECT * FROM feat_inventory_risk
    WHERE snapshot_date >= '2025-08-04'
      AND is_stocked_out = false
""").fetchdf()

inv["category"] = inv["category"].astype("category").cat.codes
for c in ["below_reorder_point", "insufficient_supply_for_leadtime",
          "low_reliability_supplier", "is_perishable"]:
    inv[c] = inv[c].astype(int)

inv["risk_score"] = rf.predict_proba(inv[features])[:, 1]
print(f"Scored {len(inv):,} snapshots")

# ── Get actual stockout events in the same test period ─────────────────
print("Loading actual test-period stockout events...")
stockouts = con.execute("""
    SELECT store_id, sku_id, stockout_date, estimated_lost_revenue,
           duration_days
    FROM fact_stockouts
    WHERE stockout_date >= '2025-08-04'
""").fetchdf()
print(f"Total test-period stockout events: {len(stockouts):,}")
print(f"Total test-period lost revenue: ${stockouts['estimated_lost_revenue'].sum():,.2f}")

# ── For each stockout, check if the model flagged risk early enough ────
lead_times = con.execute("""
    SELECT p.sku_id, s.lead_time_days_avg
    FROM dim_products p JOIN dim_suppliers s ON p.supplier_id = s.supplier_id
""").fetchdf()
stockouts = stockouts.merge(lead_times, on="sku_id", how="left")

RISK_THRESHOLD = 0.5
catchable_flags = []

inv_lookup = inv.set_index(["store_id", "sku_id", "snapshot_date"])["risk_score"]

for row in stockouts.itertuples():
    lead_time = row.lead_time_days_avg if pd.notna(row.lead_time_days_avg) else 7
    window_start = row.stockout_date - pd.Timedelta(days=14)
    window_end = row.stockout_date - pd.Timedelta(days=int(lead_time))

    try:
        candidate_dates = pd.date_range(window_start, window_end)
        was_flagged = False
        for d in candidate_dates:
            key = (row.store_id, row.sku_id, d)
            if key in inv_lookup.index and inv_lookup.loc[key] >= RISK_THRESHOLD:
                was_flagged = True
                break
        catchable_flags.append(was_flagged)
    except Exception:
        catchable_flags.append(False)

stockouts["catchable"] = catchable_flags

# ── Results ──────────────────────────────────────────────────────────
total_loss = stockouts["estimated_lost_revenue"].sum()
catchable_loss = stockouts.loc[stockouts["catchable"], "estimated_lost_revenue"].sum()
catchable_pct = round(100 * catchable_loss / total_loss, 2)
catchable_event_pct = round(100 * stockouts["catchable"].mean(), 2)

print("\n" + "="*60)
print("BACKTEST RESULTS")
print("="*60)
print(f"Test-period stockout events:        {len(stockouts):,}")
print(f"Catchable events (model flagged early): {stockouts['catchable'].sum():,} ({catchable_event_pct}%)")
print(f"Total test-period lost revenue:     ${total_loss:,.2f}")
print(f"Catchable (addressable) revenue:    ${catchable_loss:,.2f} ({catchable_pct}% of total)")

print("\n--- Applying conservative execution-success assumptions ---")
print("(catching a risk signal early doesn't guarantee full prevention —")
print(" real-world execution: order approval, supplier fulfillment, etc.)")
for rate in [0.4, 0.5, 0.6]:
    recaptured = catchable_loss * rate
    pct_of_total = round(100 * recaptured / total_loss, 2)
    print(f"  At {int(rate*100)}% execution success: ${recaptured:,.2f} recaptured ({pct_of_total}% of test-period loss)")

# Annualize: test period is ~5 months, scale to full year for headline comparison
test_days = (stockouts["stockout_date"].max() - stockouts["stockout_date"].min()).days
annualization_factor = 365 / max(test_days, 1)
print(f"\n--- Annualized (test period ≈ {test_days} days) ---")
for rate in [0.4, 0.5, 0.6]:
    annualized = catchable_loss * rate * annualization_factor
    print(f"  At {int(rate*100)}% execution success, annualized: ${annualized:,.2f}")

con.close()