import duckdb
con = duckdb.connect("../warehouse.duckdb")
print(con.execute("""
    SELECT had_shortfall, COUNT(*) FROM fact_replenishment GROUP BY had_shortfall
""").fetchdf())
print(con.execute("""
    SELECT units_ordered, units_received, had_shortfall 
    FROM fact_replenishment LIMIT 10
""").fetchdf())