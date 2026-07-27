import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, classification_report, confusion_matrix
)
import joblib

print("Loading training data...")
df = pd.read_parquet("training_data.parquet")

# ── Feature prep ─────────────────────────────────────────────
# Encode categoricals
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

# ── Time-aware split (not random!) ──────────────────────────
# Sort by date, train on earlier data, test on later — mimics real deployment
df_sorted = df.sort_values("snapshot_date")
split_idx = int(len(df_sorted) * 0.8)
train_idx = df_sorted.index[:split_idx]
test_idx = df_sorted.index[split_idx:]

X_train, X_test = X.loc[train_idx], X.loc[test_idx]
y_train, y_test = y.loc[train_idx], y.loc[test_idx]

print(f"Train: {len(X_train):,} rows | Test: {len(X_test):,} rows")
print(f"Train period: {df_sorted.loc[train_idx,'snapshot_date'].min()} to {df_sorted.loc[train_idx,'snapshot_date'].max()}")
print(f"Test period:  {df_sorted.loc[test_idx,'snapshot_date'].min()} to {df_sorted.loc[test_idx,'snapshot_date'].max()}")

# ── Baseline 1: Logistic Regression ─────────────────────────
print("\n" + "="*60)
print("BASELINE 1: Logistic Regression")
print("="*60)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

lr = LogisticRegression(max_iter=1000, class_weight="balanced")
lr.fit(X_train_scaled, y_train)
lr_pred = lr.predict(X_test_scaled)
lr_proba = lr.predict_proba(X_test_scaled)[:, 1]

print(f"Precision: {round(precision_score(y_test, lr_pred), 3)}")
print(f"Recall:    {round(recall_score(y_test, lr_pred), 3)}")
print(f"F1:        {round(f1_score(y_test, lr_pred), 3)}")
print(f"ROC-AUC:   {round(roc_auc_score(y_test, lr_proba), 3)}")

# ── Baseline 2: Random Forest ───────────────────────────────
print("\n" + "="*60)
print("BASELINE 2: Random Forest")
print("="*60)

rf = RandomForestClassifier(
    n_estimators=100, max_depth=10, class_weight="balanced",
    n_jobs=-1, random_state=42
)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_proba = rf.predict_proba(X_test)[:, 1]

print(f"Precision: {round(precision_score(y_test, rf_pred), 3)}")
print(f"Recall:    {round(recall_score(y_test, rf_pred), 3)}")
print(f"F1:        {round(f1_score(y_test, rf_pred), 3)}")
print(f"ROC-AUC:   {round(roc_auc_score(y_test, rf_proba), 3)}")

print("\nFeature importances (Random Forest):")
importances = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False)
print(importances)

# ── Naive baseline for comparison ───────────────────────────
print("\n" + "="*60)
print("NAIVE BASELINE: predict majority class (always 'no stockout')")
print("="*60)
naive_pred = pd.Series([0] * len(y_test))
print(f"Accuracy: {round((naive_pred.values == y_test.values).mean(), 3)} "
      f"(this looks good but is USELESS — catches 0% of real stockouts)")
print(f"Recall on positive class: 0.0 (by definition)")

# Save the better model
joblib.dump(rf, "model_rf_baseline.pkl")
joblib.dump(scaler, "scaler.pkl")
print("\nSaved model_rf_baseline.pkl")