import duckdb

con = duckdb.connect("warehouse.duckdb")

tables = [
    "stores",
    "products",
    "suppliers",
    "promotions",
    "store_layout",
    "stockout_events",
    "inventory_snapshots",
    "replenishment_logs",
    "sales_transactions",
    "demand_forecasts",
]

for name in tables:
    path = f"raw_data/{name}.csv"
    con.execute(f"""
        CREATE OR REPLACE TABLE raw_{name} AS
        SELECT * FROM read_csv_auto('{path}', union_by_name=true)
    """)
    count = con.execute(f"SELECT COUNT(*) FROM raw_{name}").fetchone()[0]
    print(f"{name:25s} -> {count:,} rows loaded")

con.close()
print("\nAll tables loaded into warehouse.duckdb")