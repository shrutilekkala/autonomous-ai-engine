import duckdb
con = duckdb.connect("../warehouse.duckdb")

print("--- avg_shortfall_pct stats ---")
df = con.execute("SELECT avg_shortfall_pct, shortfall_volatility FROM feat_replenishment_signals").fetchdf()
print(df.describe())

print("\n--- Does shortfall_pct correlate with stockout risk? ---")
combined = con.execute("""
    SELECT
        rs.avg_shortfall_pct,
        rs.shortfall_volatility,
        fi.is_stocked_out
    FROM feat_replenishment_signals rs
    JOIN feat_inventory_risk fi
      ON rs.store_id = fi.store_id AND rs.sku_id = fi.sku_id
""").fetchdf()

grouped = combined.groupby('is_stocked_out')[['avg_shortfall_pct','shortfall_volatility']].mean()
print(grouped)

print(f"\nCorrelation (avg_shortfall_pct vs is_stocked_out): "
      f"{round(combined['avg_shortfall_pct'].corr(combined['is_stocked_out'].astype(int)), 3)}")
print(f"Correlation (shortfall_volatility vs is_stocked_out): "
      f"{round(combined['shortfall_volatility'].corr(combined['is_stocked_out'].astype(int)), 3)}")

con.close()