import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import lightgbm as lgb
import joblib
import time

print("Loading forecast data...")
df = pd.read_parquet("forecast_data.parquet")

# Encode categoricals
for col in ["category", "region", "foot_traffic_tier"]:
    df[col] = df[col].astype("category").cat.codes
df["is_weekend"] = df["is_weekend"].astype(int)
df["is_december"] = df["is_december"].astype(int)
df["is_holiday_season"] = df["is_holiday_season"].astype(int)
df["is_perishable"] = df["is_perishable"].astype(int)

features = [
    "month", "day_of_week", "is_weekend", "is_december", "is_holiday_season",
    "region", "foot_traffic_tier", "category", "is_perishable",
    "units_lag_1d", "units_lag_7d", "units_rolling_avg_7d", "units_rolling_avg_30d",
]
X = df[features]
y = df["daily_units_sold"]

# Time-aware split, same principle as the classifier
df_sorted = df.sort_values("sale_date")
split_idx = int(len(df_sorted) * 0.8)
train_idx = df_sorted.index[:split_idx]
test_idx = df_sorted.index[split_idx:]

X_train, X_test = X.loc[train_idx], X.loc[test_idx]
y_train, y_test = y.loc[train_idx], y.loc[test_idx]

print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")

def evaluate(name, pred):
    mae = mean_absolute_error(y_test, pred)
    mape = mean_absolute_percentage_error(y_test.clip(lower=1), np.clip(pred, 1, None)) * 100
    print(f"{name:35s} MAE={round(mae,3):<8} MAPE={round(mape,2)}%")
    return mae, mape

print("\n" + "="*60)
print("NAIVE BASELINES")
print("="*60)
evaluate("Naive: same as 7 days ago", X_test["units_lag_7d"])
evaluate("Naive: 7-day rolling avg", X_test["units_rolling_avg_7d"])
evaluate("Naive: 30-day rolling avg", X_test["units_rolling_avg_30d"])

print("\n" + "="*60)
print("LIGHTGBM")
print("="*60)
t0 = time.time()
lgb_model = lgb.LGBMRegressor(n_estimators=200, max_depth=8, learning_rate=0.1, n_jobs=-1, random_state=42, verbose=-1)
lgb_model.fit(X_train, y_train)
lgb_pred = lgb_model.predict(X_test)
print(f"Trained in {round(time.time()-t0,1)}s")
evaluate("LightGBM", lgb_pred)

joblib.dump(lgb_model, "model_forecast_lgb.pkl")
print("\nSaved forecasting model")
