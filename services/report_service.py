import os
import pandas as pd

from services.i18n import tr

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def build_excel_report(prediction, lang=None):
    """Excel report with headers and values in the visitor's language (English if lang is None and no request)."""
    T = lambda text: tr(text, lang)
    day, loc, temp, hum, rain, irr, water = (T(x) for x in (
        "Day", "Location", "Temperature", "Humidity", "Rainfall", "Irrigation", "Water (L)"))
    rows = [{
        day: T("Today"), loc: prediction.location, temp: prediction.temperature,
        hum: prediction.humidity, rain: prediction.rainfall,
        irr: T(prediction.alert), water: prediction.water_today,
    }]
    for d in prediction.week_prediction or []:
        rows.append({
            day: T(d["day"]), loc: prediction.location, temp: "-",
            hum: "-", rain: "-", irr: T(d["irrigation"]), water: d["water"],
        })
    df = pd.DataFrame(rows)
    file_path = os.path.join(REPORTS_DIR, f"Smart_Irrigation_Report_{prediction.id}.xlsx")
    df.to_excel(file_path, index=False)
    return file_path
