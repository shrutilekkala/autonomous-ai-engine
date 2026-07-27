import pandas as pd
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score
)
import xgboost as xgb
import lightgbm as lgb
import joblib
import time

print("Loading training data...")
df = pd.read_parquet("training_data.parquet")

df["category"] = df["category"].astype("category").cat.codes
df["below_reorder_point"] = df["below_reorder_point"].astype(int)
df["insufficient_supply_for_leadtime"] = df["insufficient_supply_for_leadtime"].astype(int)
df["low_reliability_supplier"] = df["low_reliability_supplier"].astype(int)
df["is_perishable"] = df["is_perishable"].astype(int)

features = [
    "units_on_hand", "units_in_backroom", "days_of_supply",
    "reorder_point", "safety_stock", "below_reorder_point",
    "insufficient_supply_for_leadtime", "low_reliability_supplier",
    "is_perishable", "category", "reliability_score", "lead_time_days_avg",
]
X = df[features]
y = df["stockout_within_14d"]

# Same time-aware split as the baseline, for a fair comparison
df_sorted = df.sort_values("snapshot_date")
split_idx = int(len(df_sorted) * 0.8)
train_idx = df_sorted.index[:split_idx]
test_idx = df_sorted.index[split_idx:]

X_train, X_test = X.loc[train_idx], X.loc[test_idx]
y_train, y_test = y.loc[train_idx], y.loc[test_idx]

# Class imbalance ratio for scale_pos_weight (XGBoost) / class weighting (LightGBM)
neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
scale_pos_weight = neg / pos
print(f"Class ratio (neg/pos): {round(scale_pos_weight, 2)}")

# ── XGBoost ──────────────────────────────────────────────────
print("\n" + "="*60)
print("XGBoost")
print("="*60)
t0 = time.time()

xgb_model = xgb.XGBClassifier(
    n_estimators=200, max_depth=6, learning_rate=0.1,
    scale_pos_weight=scale_pos_weight,
    eval_metric="logloss", n_jobs=-1, random_state=42
)
xgb_model.fit(X_train, y_train)
xgb_pred = xgb_model.predict(X_test)
xgb_proba = xgb_model.predict_proba(X_test)[:, 1]

print(f"Trained in {round(time.time()-t0,1)}s")
print(f"Precision: {round(precision_score(y_test, xgb_pred), 3)}")
print(f"Recall:    {round(recall_score(y_test, xgb_pred), 3)}")
print(f"F1:        {round(f1_score(y_test, xgb_pred), 3)}")
print(f"ROC-AUC:   {round(roc_auc_score(y_test, xgb_proba), 3)}")

print("\nFeature importances (XGBoost):")
imp = pd.Series(xgb_model.feature_importances_, index=features).sort_values(ascending=False)
print(imp)

# ── LightGBM ─────────────────────────────────────────────────
print("\n" + "="*60)
print("LightGBM")
print("="*60)
t0 = time.time()

lgb_model = lgb.LGBMClassifier(
    n_estimators=200, max_depth=6, learning_rate=0.1,
    class_weight="balanced", n_jobs=-1, random_state=42, verbose=-1
)
lgb_model.fit(X_train, y_train)
lgb_pred = lgb_model.predict(X_test)
lgb_proba = lgb_model.predict_proba(X_test)[:, 1]

print(f"Trained in {round(time.time()-t0,1)}s")
print(f"Precision: {round(precision_score(y_test, lgb_pred), 3)}")
print(f"Recall:    {round(recall_score(y_test, lgb_pred), 3)}")
print(f"F1:        {round(f1_score(y_test, lgb_pred), 3)}")
print(f"ROC-AUC:   {round(roc_auc_score(y_test, lgb_proba), 3)}")

# ── Summary comparison ──────────────────────────────────────
print("\n" + "="*60)
print("SUMMARY — all models")
print("="*60)
print(f"{'Model':<25}{'Precision':<12}{'Recall':<12}{'F1':<12}{'ROC-AUC':<10}")
print(f"{'Logistic Regression':<25}{'0.459':<12}{'0.951':<12}{'0.619':<12}{'0.956':<10}")
print(f"{'Random Forest':<25}{'0.454':<12}{'0.957':<12}{'0.616':<12}{'0.959':<10}")
print(f"{'XGBoost':<25}{round(precision_score(y_test,xgb_pred),3):<12}{round(recall_score(y_test,xgb_pred),3):<12}{round(f1_score(y_test,xgb_pred),3):<12}{round(roc_auc_score(y_test,xgb_proba),3):<10}")
print(f"{'LightGBM':<25}{round(precision_score(y_test,lgb_pred),3):<12}{round(recall_score(y_test,lgb_pred),3):<12}{round(f1_score(y_test,lgb_pred),3):<12}{round(roc_auc_score(y_test,lgb_proba),3):<10}")

joblib.dump(xgb_model, "model_xgb.pkl")
joblib.dump(lgb_model, "model_lgb.pkl")
print("\nSaved model_xgb.pkl and model_lgb.pkl")