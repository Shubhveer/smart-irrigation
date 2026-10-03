import os
import pandas as pd

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def build_excel_report(prediction):
    rows = [{
        "Day": "Today", "Location": prediction.location, "Temperature": prediction.temperature,
        "Humidity": prediction.humidity, "Rainfall": prediction.rainfall,
        "Irrigation": prediction.alert, "Water (L)": prediction.water_today,
    }]
    for d in prediction.week_prediction or []:
        rows.append({
            "Day": d["day"], "Location": prediction.location, "Temperature": "-",
            "Humidity": "-", "Rainfall": "-", "Irrigation": d["irrigation"], "Water (L)": d["water"],
        })
    df = pd.DataFrame(rows)
    file_path = os.path.join(REPORTS_DIR, f"Smart_Irrigation_Report_{prediction.id}.xlsx")
    df.to_excel(file_path, index=False)
    return file_path
