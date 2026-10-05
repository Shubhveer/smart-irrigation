import os
import logging
import joblib
import numpy as np

logger = logging.getLogger(__name__)

# The app stores short codes in the database; these are the sentences shown to the farmer (translated on display).
ALERT_TEXT = {
    "LOW_HUMIDITY": "Humidity is low, so the soil can dry out faster than usual.",
    "HIGH_TEMP": "Temperature is high. Plants lose more water in the heat.",
    "RAIN_EXPECTED": "Rainfall is more than 5 mm, so irrigation may not be needed.",
}
RECOMMENDATION_TEXT = {
    "IRRIGATE_TIME": "Water early morning or evening rather than during peak heat.",
    "CHECK_SOIL": "Check soil moisture around the root zone before watering.",
    "AVOID_RAIN": "Rain is expected. Consider waiting before irrigation.",
}


def alert_message(code):
    return ALERT_TEXT.get(code, code)


def recommendation_message(code):
    return RECOMMENDATION_TEXT.get(code, code)
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "irrigation_model.pkl")
_model = None

def load_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        logger.info("Irrigation model loaded from %s", MODEL_PATH)
    return _model

def predict_irrigation(temp, humidity, rainfall, soil, stage):
    model = load_model()
    features = np.array([[temp, humidity, rainfall, soil, stage]])
    return int(model.predict(features)[0])

def build_today_result(temp, humidity, rainfall, soil, stage, field_size):
    irrigation = predict_irrigation(temp, humidity, rainfall, soil, stage)
    alert = "Irrigation Required" if irrigation else "No Irrigation Needed"
    water = round(500 * field_size, 2) if irrigation else 0

    weather_alerts = []
    if humidity < 40: weather_alerts.append("LOW_HUMIDITY")
    if temp > 35: weather_alerts.append("HIGH_TEMP")
    if rainfall > 5: weather_alerts.append("RAIN_EXPECTED")

    recommendations = []
    if irrigation:
        recommendations.append("IRRIGATE_TIME")
        recommendations.append("CHECK_SOIL")
    if rainfall > 5:
        recommendations.append("AVOID_RAIN")

    return {
        "irrigation": irrigation, "alert": alert, "water_today": water,
        "weather_alerts": weather_alerts, "recommendations": recommendations,
    }

def build_week_prediction(forecast_data, soil, stage, field_size):
    week = []
    for day in forecast_data:
        irrigation = predict_irrigation(day["temp"], day["humidity"], day["rainfall"], soil, stage)
        week.append({
            "day": day["day"],
            "irrigation": "Irrigation Required" if irrigation else "No Irrigation",
            "water": round(400 * field_size if irrigation else 0, 2),
        })
    return week
