import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import xgboost as xgb
import joblib
import time

print("Loading forecast data...")
df = pd.read_parquet("forecast_data.parquet")

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

df_sorted = df.sort_values("sale_date")
split_idx = int(len(df_sorted) * 0.8)
train_idx = df_sorted.index[:split_idx]
test_idx = df_sorted.index[split_idx:]

X_train, X_test = X.loc[train_idx], X.loc[test_idx]
y_train, y_test = y.loc[train_idx], y.loc[test_idx]

print(f"Train: {len(X_train):,} | Test: {len(X_test):,}")

print("\n" + "="*60)
print("XGBoost (forecasting)")
print("="*60)
t0 = time.time()

xgb_model = xgb.XGBRegressor(
    n_estimators=200, max_depth=8, learning_rate=0.1,
    tree_method="hist",   # memory-efficient histogram method, same reasoning as why we dropped RF
    n_jobs=-1, random_state=42
)
xgb_model.fit(X_train, y_train)
xgb_pred = xgb_model.predict(X_test)

elapsed = round(time.time()-t0, 1)
mae = mean_absolute_error(y_test, xgb_pred)
mape = mean_absolute_percentage_error(y_test.clip(lower=1), np.clip(xgb_pred, 1, None)) * 100

print(f"Trained in {elapsed}s")
print(f"MAE:  {round(mae,3)}")
print(f"MAPE: {round(mape,2)}%")

print(f"\nCompare to LightGBM: MAE=2.685, MAPE=40.95%")
print(f"Compare to best naive (30d rolling avg): MAE=3.016, MAPE=42.56%")

joblib.dump(xgb_model, "model_forecast_xgb.pkl")
print("\nSaved model_forecast_xgb.pkl")