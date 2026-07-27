import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ── Setup ─────────────────────────────────────────────────────────
con = duckdb.connect("../warehouse.duckdb")
os.makedirs("eda_outputs", exist_ok=True)
sns.set_style("whitegrid")

def save(fig, name):
    fig.savefig(f"eda_outputs/{name}.png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    print(f"Saved eda_outputs/{name}.png")

print("="*60)
print("1. MISSING VALUE AUDIT")
print("="*60)

tables = ["fact_sales", "fact_stockouts", "fact_inventory",
          "fact_replenishment", "dim_stores", "dim_products", "dim_suppliers"]

for t in tables:
    cols = con.execute(f"DESCRIBE {t}").fetchdf()["column_name"].tolist()
    total = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"\n{t} (total rows: {total:,})")
    for c in cols:
        nulls = con.execute(f"SELECT COUNT(*) FROM {t} WHERE {c} IS NULL").fetchone()[0]
        if nulls > 0:
            pct = round(100*nulls/total, 2)
            print(f"  {c:25s} -> {nulls:,} nulls ({pct}%)")

print("\n" + "="*60)
print("2. NUMERIC DISTRIBUTIONS (key columns)")
print("="*60)

dist_checks = {
    "fact_sales": ["units_sold", "unit_price_actual", "revenue", "gross_margin"],
    "fact_stockouts": ["duration_days", "estimated_lost_units", "estimated_lost_revenue"],
    "fact_inventory": ["days_of_supply", "units_on_hand", "units_in_backroom"],
    "fact_replenishment": ["lead_time_actual", "lead_time_variance", "replenishment_cost"],
}

for table, cols in dist_checks.items():
    df = con.execute(f"SELECT {', '.join(cols)} FROM {table} USING SAMPLE 200000").fetchdf()
    print(f"\n--- {table} ---")
    print(df.describe())

    fig, axes = plt.subplots(1, len(cols), figsize=(5*len(cols), 4))
    if len(cols) == 1:
        axes = [axes]
    for ax, c in zip(axes, cols):
        sns.histplot(df[c].dropna(), ax=ax, bins=50, kde=True)
        ax.set_title(c)
    fig.suptitle(f"{table} distributions")
    save(fig, f"dist_{table}")

print("\n" + "="*60)
print("3. OUTLIER DETECTION (IQR method)")
print("="*60)

outlier_checks = {
    "fact_sales": "units_sold",
    "fact_stockouts": "duration_days",
    "fact_replenishment": "lead_time_actual",
}

for table, col in outlier_checks.items():
    q1, q3 = con.execute(f"""
        SELECT quantile_cont({col}, 0.25), quantile_cont({col}, 0.75)
        FROM {table}
    """).fetchone()
    iqr = q3 - q1
    lower, upper = q1 - 1.5*iqr, q3 + 1.5*iqr
    n_outliers = con.execute(f"""
        SELECT COUNT(*) FROM {table}
        WHERE {col} < {lower} OR {col} > {upper}
    """).fetchone()[0]
    total = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}.{col}: {n_outliers:,} outliers ({round(100*n_outliers/total,2)}%) "
          f"outside [{round(lower,2)}, {round(upper,2)}]")

print("\n" + "="*60)
print("4. CORRELATION ANALYSIS")
print("="*60)

# Lead time variance vs stockout duration (via shared store+sku)
corr_df = con.execute("""
    SELECT
        r.lead_time_variance,
        s.duration_days
    FROM fact_replenishment r
    JOIN fact_stockouts s
      ON r.store_id = s.store_id AND r.sku_id = s.sku_id
    USING SAMPLE 100000
""").fetchdf()
corr_val = corr_df["lead_time_variance"].corr(corr_df["duration_days"])
print(f"Correlation (lead_time_variance vs stockout duration_days): {round(corr_val,3)}")

fig, ax = plt.subplots(figsize=(6,5))
sns.scatterplot(data=corr_df.sample(min(5000,len(corr_df))), x="lead_time_variance", y="duration_days", alpha=0.3, ax=ax)
ax.set_title(f"Lead Time Variance vs Stockout Duration (corr={round(corr_val,3)})")
save(fig, "corr_leadtime_vs_duration")

# Foot traffic tier vs revenue per SKU
ft_rev = con.execute("""
    SELECT st.foot_traffic_tier, AVG(f.revenue) as avg_revenue
    FROM fact_sales f
    JOIN dim_stores st ON f.store_id = st.store_id
    GROUP BY st.foot_traffic_tier
    ORDER BY avg_revenue DESC
""").fetchdf()
print("\nAvg revenue per transaction by foot traffic tier:")
print(ft_rev)

fig, ax = plt.subplots(figsize=(6,4))
sns.barplot(data=ft_rev, x="foot_traffic_tier", y="avg_revenue", ax=ax)
ax.set_title("Avg Revenue per Transaction by Foot Traffic Tier")
save(fig, "revenue_by_foot_traffic")

print("\n" + "="*60)
print("5. TIME SERIES PATTERNS")
print("="*60)

monthly = con.execute("""
    SELECT date_trunc('month', sale_date) as month, SUM(revenue) as revenue
    FROM fact_sales
    GROUP BY 1 ORDER BY 1
""").fetchdf()

fig, ax = plt.subplots(figsize=(10,4))
ax.plot(monthly["month"], monthly["revenue"], marker="o")
ax.set_title("Monthly Revenue Trend")
ax.tick_params(axis='x', rotation=45)
save(fig, "monthly_revenue_trend")

dow = con.execute("""
    SELECT dayname(sale_date) as day_of_week, AVG(revenue) as avg_revenue
    FROM fact_sales
    GROUP BY 1
""").fetchdf()
order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
dow["day_of_week"] = pd.Categorical(dow["day_of_week"], categories=order, ordered=True)
dow = dow.sort_values("day_of_week")

fig, ax = plt.subplots(figsize=(7,4))
sns.barplot(data=dow, x="day_of_week", y="avg_revenue", ax=ax)
ax.set_title("Avg Revenue by Day of Week")
ax.tick_params(axis='x', rotation=45)
save(fig, "revenue_by_day_of_week")

print("\n" + "="*60)
print("EDA COMPLETE — check eda/eda_outputs/ for all charts")
print("="*60)

con.close()