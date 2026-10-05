"""
Train the irrigation model on a REAL dataset (no synthetic data).

Dataset: Smart Agriculture Dataset (Kaggle, chaitanyagopidesi/smart-agriculture-dataset)
Save the CSV as  eda/data/smart_agriculture_dataset.csv  (see eda/data/README.md), then:

    python train_model.py                 # features: temp, humidity, soil, stage
    python train_model.py --with-moi      # also use soil moisture (MOI) if your form collects it

Output: models/irrigation_real.joblib  (model + feature list + category lists)
The currently deployed irrigation_model.pkl is NOT overwritten.
"""
import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42
CSV = Path("eda/data/smart_agriculture_dataset.csv")
OUT = Path("models/irrigation_real.joblib")

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default=str(CSV))
ap.add_argument("--with-moi", action="store_true")
args = ap.parse_args()

if not Path(args.csv).exists():
    sys.exit(f"Dataset not found: {args.csv}\nDownload the real CSV from Kaggle first (see eda/data/README.md).")

df = pd.read_csv(args.csv)
df.columns = [c.strip().replace(" ", "_") for c in df.columns]
df = df.rename(columns={"Seedling_Stage": "stage", "soil_type": "soil"})
required = {"temp", "humidity", "soil", "stage", "result"} | ({"MOI"} if args.with_moi else set())
missing = required - set(df.columns)
if missing:
    sys.exit(f"CSV is missing columns: {sorted(missing)}. Found: {list(df.columns)}")

before = len(df)
df = df.dropna(subset=list(required)).drop_duplicates()
print(f"Rows: {before} -> {len(df)} after dropping missing/duplicates")
print("Target balance:\n", df["result"].value_counts(normalize=True).round(3).to_string())

soil_classes = sorted(df["soil"].astype(str).unique())
stage_classes = sorted(df["stage"].astype(str).unique())
df["soil_enc"] = df["soil"].astype(str).map({c: i for i, c in enumerate(soil_classes)})
df["stage_enc"] = df["stage"].astype(str).map({c: i for i, c in enumerate(stage_classes)})

features = ["temp", "humidity", "soil_enc", "stage_enc"] + (["MOI"] if args.with_moi else [])
X, y = df[features], df["result"].astype(int)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)

candidates = {
    "LogisticRegression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
    "RandomForest": RandomForestClassifier(n_estimators=200, min_samples_leaf=2, n_jobs=-1, random_state=SEED),
    "GradientBoosting": GradientBoostingClassifier(random_state=SEED),
}
cv = StratifiedKFold(5, shuffle=True, random_state=SEED)
scores = {n: cross_val_score(m, X_tr, y_tr, cv=cv, scoring="f1").mean() for n, m in candidates.items()}
for n, s in scores.items():
    print(f"CV F1  {n:20s} {s:.4f}")
best_name = max(scores, key=scores.get)
model = candidates[best_name].fit(X_tr, y_tr)

pred = model.predict(X_te)
print(f"\nBest: {best_name}\nTEST F1: {f1_score(y_te, pred):.4f}  "
      f"AUC: {roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]):.4f}")
print(classification_report(y_te, pred))

OUT.parent.mkdir(exist_ok=True)
joblib.dump({"model": model, "features": features, "soil_classes": soil_classes,
             "stage_classes": stage_classes, "model_name": best_name}, OUT)
print(f"Saved {OUT}\nSoil categories : {soil_classes}\nStage categories: {stage_classes}")
