import duckdb
con = duckdb.connect("../warehouse.duckdb")

print("="*60)
print("1. Does lead_time_volatility predict shortfall rate?")
print("="*60)
df1 = con.execute("""
    SELECT lead_time_volatility, shortfall_rate_pct
    FROM feat_replenishment_signals
    WHERE lead_time_volatility IS NOT NULL
""").fetchdf()
print(f"Correlation: {round(df1['lead_time_volatility'].corr(df1['shortfall_rate_pct']), 3)}")
print(df1.describe())

print("\n" + "="*60)
print("2. Does insufficient_supply_for_leadtime predict actual stockouts?")
print("="*60)
df2 = con.execute("""
    SELECT
        fr.insufficient_supply_for_leadtime,
        COUNT(*) as inventory_snapshots,
        SUM(CASE WHEN fr.is_stocked_out THEN 1 ELSE 0 END) as stocked_out_count,
        ROUND(100.0*SUM(CASE WHEN fr.is_stocked_out THEN 1 ELSE 0 END)/COUNT(*), 2) as stockout_rate_pct
    FROM feat_inventory_risk fr
    GROUP BY fr.insufficient_supply_for_leadtime
""").fetchdf()
print(df2)

print("\n" + "="*60)
print("3. Does low_reliability_supplier predict actual stockouts?")
print("="*60)
df3 = con.execute("""
    SELECT
        fr.low_reliability_supplier,
        COUNT(*) as inventory_snapshots,
        SUM(CASE WHEN fr.is_stocked_out THEN 1 ELSE 0 END) as stocked_out_count,
        ROUND(100.0*SUM(CASE WHEN fr.is_stocked_out THEN 1 ELSE 0 END)/COUNT(*), 2) as stockout_rate_pct
    FROM feat_inventory_risk fr
    GROUP BY fr.low_reliability_supplier
""").fetchdf()
print(df3)

print("\n" + "="*60)
print("4. Does is_weekend / is_holiday_season actually move daily sales?")
print("="*60)
df4 = con.execute("""
    SELECT is_weekend, AVG(daily_units_sold) as avg_units
    FROM feat_sales_daily GROUP BY is_weekend
""").fetchdf()
print("Weekend effect:\n", df4)

df5 = con.execute("""
    SELECT is_holiday_season, AVG(daily_units_sold) as avg_units
    FROM feat_sales_daily GROUP BY is_holiday_season
""").fetchdf()
print("\nHoliday season effect:\n", df5)

con.close()