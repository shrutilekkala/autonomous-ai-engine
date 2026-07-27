import duckdb
con = duckdb.connect("../warehouse.duckdb")

print("--- Does shortfall_pct correlate with replenishment cost? ---")
df = con.execute("""
    SELECT avg_shortfall_pct, shortfall_volatility, avg_replenishment_cost, emergency_order_count
    FROM feat_replenishment_signals
""").fetchdf()

print(f"Correlation (avg_shortfall_pct vs avg_replenishment_cost): "
      f"{round(df['avg_shortfall_pct'].corr(df['avg_replenishment_cost']), 3)}")
print(f"Correlation (shortfall_volatility vs avg_replenishment_cost): "
      f"{round(df['shortfall_volatility'].corr(df['avg_replenishment_cost']), 3)}")
print(f"Correlation (avg_shortfall_pct vs emergency_order_count): "
      f"{round(df['avg_shortfall_pct'].corr(df['emergency_order_count']), 3)}")

con.close()