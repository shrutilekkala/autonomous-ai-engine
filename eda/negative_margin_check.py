import duckdb
con = duckdb.connect("../warehouse.duckdb")

print(con.execute("""
    SELECT f.transaction_id, f.store_id, f.sku_id, p.category,
           f.unit_price_actual, p.unit_cost, f.units_sold, f.gross_margin, f.is_promoted
    FROM fact_sales f
    JOIN dim_products p ON f.sku_id = p.sku_id
    WHERE f.gross_margin < 0
    ORDER BY f.gross_margin ASC
    LIMIT 15
""").fetchdf())

print(con.execute("""
    SELECT COUNT(*) as negative_margin_txns,
           ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM fact_sales), 3) as pct_of_all_txns,
           SUM(gross_margin) as total_negative_margin_impact
    FROM fact_sales
    WHERE gross_margin < 0
""").fetchdf())