import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from train_model import load_data, build_pipeline, FEATURES, TARGET
from sklearn.model_selection import train_test_split
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, accuracy_score, f1_score
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DATA=ROOT/"eda/data/raw/smart_agriculture_dataset.csv"
REPORT_DIR=ROOT/"eda/reports"
def save_plot(name):
    REPORT_DIR.mkdir(parents=True,exist_ok=True)
    plt.tight_layout(); plt.savefig(REPORT_DIR/name,dpi=160,bbox_inches="tight"); plt.close()
def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--data",type=Path,default=DEFAULT_DATA); args=parser.parse_args()
    raw=pd.read_csv(args.data); print("1) RAW DATA",raw.shape); print(raw.head())
    print("2) MISSING VALUES"); print(raw.isna().sum()); print("Duplicates:",raw.duplicated().sum())
    df=load_data(args.data); print("3) CLEAN DATA",df.shape); print(df.describe(include="all").transpose())
    plt.figure(figsize=(7,4)); sns.countplot(data=df,x=TARGET); plt.title("Irrigation Decision Distribution"); save_plot("01_target_distribution.png")
    for col in ["MOI","temp","humidity"]:
        plt.figure(figsize=(7,4)); sns.histplot(df[col],kde=True); plt.title(f"{col} distribution"); save_plot(f"02_{col}_distribution.png")
    for col in ["soil_type","Seedling Stage"]:
        plt.figure(figsize=(9,4)); sns.countplot(data=df,x=col,order=df[col].value_counts().index); plt.xticks(rotation=30,ha="right"); plt.title(f"{col} distribution"); save_plot(f"03_{col}_distribution.png")
    plt.figure(figsize=(7,5)); sns.heatmap(df[["MOI","temp","humidity",TARGET]].corr(),annot=True,fmt=".2f"); plt.title("Numeric Feature Correlation"); save_plot("04_correlation.png")
    for col in ["MOI","temp","humidity"]:
        plt.figure(figsize=(7,4)); sns.boxplot(data=df,x=TARGET,y=col); plt.title(f"{col} by irrigation decision"); save_plot(f"05_{col}_by_target.png")
    X,y=df[FEATURES],df[TARGET]; X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.20,random_state=42,stratify=y)
    model=build_pipeline(); model.fit(X_train,y_train); pred=model.predict(X_test)
    print("4) TEST RESULTS"); print("Accuracy:",round(accuracy_score(y_test,pred),4)); print("Macro F1:",round(f1_score(y_test,pred,average="macro"),4)); print(classification_report(y_test,pred,zero_division=0))
    ConfusionMatrixDisplay.from_predictions(y_test,pred); plt.title("Irrigation Decision Confusion Matrix"); save_plot("06_confusion_matrix.png")
if __name__=="__main__": main()