"""Train Farm Saathi irrigation model on the real Smart Agriculture dataset."""
import argparse
from pathlib import Path
import joblib, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
ROOT=Path(__file__).resolve().parent
DEFAULT_DATA=ROOT/"eda/data/raw/smart_agriculture_dataset.csv"
MODEL_PATH=ROOT/"irrigation_model.pkl"
FEATURES=["soil_type","Seedling Stage","MOI","temp","humidity"]; TARGET="result"
def load_data(path):
    if not path.exists(): raise FileNotFoundError(f"Dataset not found: {path}. Download the real Smart Agriculture Dataset from Kaggle and place it there.")
    df=pd.read_csv(path); required=FEATURES+[TARGET]; missing=[c for c in required if c not in df.columns]
    if missing: raise ValueError(f"Missing required columns: {missing}")
    df=df[required].copy().drop_duplicates()
    for col in ["MOI","temp","humidity",TARGET]: df[col]=pd.to_numeric(df[col],errors="coerce")
    df=df.dropna(subset=[TARGET]); df[TARGET]=df[TARGET].astype(int)
    unexpected=sorted(set(df[TARGET])-{0,1,2})
    if unexpected: raise ValueError(f"Unexpected target values: {unexpected}")
    return df
def build_pipeline():
    cat=["soil_type","Seedling Stage"]; num=["MOI","temp","humidity"]
    prep=ColumnTransformer([("cat",Pipeline([("imputer",SimpleImputer(strategy="most_frequent")),("onehot",OneHotEncoder(handle_unknown="ignore"))]),cat),("num",Pipeline([("imputer",SimpleImputer(strategy="median")),("scale",StandardScaler())]),num)])
    return Pipeline([("preprocess",prep),("model",RandomForestClassifier(n_estimators=300,random_state=42,class_weight="balanced",n_jobs=-1))])
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--data",type=Path,default=DEFAULT_DATA); args=parser.parse_args()
    df=load_data(args.data); X,y=df[FEATURES],df[TARGET]
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.20,random_state=42,stratify=y)
    model=build_pipeline(); model.fit(X_train,y_train); pred=model.predict(X_test)
    print(f"Rows after cleaning: {len(df)}"); print(y.value_counts().sort_index()); print(f"Accuracy: {accuracy_score(y_test,pred):.4f}"); print(f"Macro F1: {f1_score(y_test,pred,average="macro"):.4f}")
    print(classification_report(y_test,pred,zero_division=0)); print(confusion_matrix(y_test,pred))
    joblib.dump(model,MODEL_PATH); print(f"Saved REAL-DATA model to: {MODEL_PATH}")
if __name__=="__main__": main()