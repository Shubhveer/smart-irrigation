# EDA & Model Comparison

This folder contains the data science side of the project, separate from the
Flask web app — exploring a real dataset, comparing models honestly, and
documenting the reasoning, rather than just shipping a single hardcoded model.

## Setup

```bash
cd eda
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install -r requirements-eda.txt
jupyter notebook smart_irrigation_eda.ipynb
```

## Dataset

**[Smart Agriculture Dataset](https://www.kaggle.com/datasets/chaitanyagopidesi/smart-agriculture-dataset)**
(Kaggle, 16,411 records) — soil type, crop growth stage, soil moisture index
(MOI), temperature, humidity, and a binary irrigation-required label.

`data/smart_agriculture_dataset.csv` currently contains a **stand-in dataset**
with the exact same column structure, generated so the notebook is fully
runnable out of the box. To use the real data:

1. Download the CSV from the Kaggle link above
2. Replace `data/smart_agriculture_dataset.csv` with it (same filename, same
   columns — no notebook code changes needed)
3. Re-run all cells

## What's inside the notebook

1. Load, inspect, clean (missing values, duplicates)
2. Target balance check
3. Distribution plots, boxplots by outcome, categorical breakdowns
4. Correlation heatmap
5. Encode categorical features
6. Train/test split (stratified)
7. **Compare 6 models**: Logistic Regression, KNN, Decision Tree, Random
   Forest, SVM, Gradient Boosting — same split, same metrics, no cherry-picking
8. ROC curves, confusion matrix, classification report
9. Feature importance
10. Hyperparameter tuning (GridSearchCV) on the winning model
11. Final model saved to `model/irrigation_model_v2.pkl`

## Integrating a retrained model back into the Flask app

This dataset uses **soil moisture % (MOI)** instead of rainfall. The main
app's form doesn't currently collect that. See Section 17 of the notebook
for the two integration options (add a simple dry/normal/damp dropdown to
the form, or retrain without MOI to keep the current form unchanged).
