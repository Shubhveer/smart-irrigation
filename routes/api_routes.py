import logging

from flask import Blueprint, request, jsonify

from database.db import SessionLocal
from database.models import Prediction
from services import weather_service, irrigation_service
from services.i18n import LANGS, M, get_lang, tr

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/irrigation", methods=["POST"])
def irrigation():

    data = request.get_json(silent=True)
    # Language for the text in the response: JSON field "lang", ?lang=, Accept-Language header, else English
    lang = data.get("lang") if isinstance(data, dict) and data.get("lang") in LANGS else get_lang()

    if not data:
        return jsonify({
            "success": False,
            "error": tr("Request body must contain JSON.", lang)
        }), 400

    location = str(data.get("location", "")).strip()

    soil_raw = data.get("soil_type")
    stage_raw = data.get("crop_stage")
    size_raw = data.get("field_size", 1.0)

    if not location:
        return jsonify({
            "success": False,
            "error": tr("Location is required.", lang)
        }), 400

    if soil_raw is None or stage_raw is None:
        return jsonify({
            "success": False,
            "error": tr("Soil type and crop stage are required.", lang)
        }), 400

    try:
        soil = int(soil_raw)
        stage = int(stage_raw)
        field_size = float(size_raw)

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": tr("Soil type, crop stage and field size must be valid numbers.", lang)
        }), 400

    try:
        # Get current weather
        weather = weather_service.get_weather(location)

        # Get forecast
        forecast_data = weather_service.get_forecast(location)

        # Calculate today's irrigation
        today = irrigation_service.build_today_result(
            weather["temperature"],
            weather["humidity"],
            weather["rainfall"],
            soil,
            stage,
            field_size
        )

        # Calculate weekly prediction
        week = irrigation_service.build_week_prediction(
            forecast_data,
            soil,
            stage,
            field_size
        )

    except weather_service.WeatherServiceError as e:

        logger.warning(
            "Weather lookup failed for %s: %s",
            location,
            e
        )

        return jsonify({
            "success": False,
            "error": tr(M("Could not fetch weather for '{location}'.", location=location), lang)
        }), 502

    except Exception:
        logger.exception("Irrigation API failed")

        return jsonify({
            "success": False,
            "error": tr("Unable to generate irrigation advice.", lang)
        }), 500

    # Save prediction to database
    db = SessionLocal()

    try:
        record = Prediction(
            location=location,
            soil_type=soil,
            crop_stage=stage,
            field_size=field_size,
            temperature=weather["temperature"],
            humidity=weather["humidity"],
            rainfall=weather["rainfall"],
            alert=today["alert"],
            water_today=today["water_today"],
            weather_alerts=today["weather_alerts"],
            recommendations=today["recommendations"],
            week_prediction=week,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        prediction_id = record.id

    except Exception:
        db.rollback()
        logger.exception("Could not save irrigation prediction")
        prediction_id = None

    finally:
        db.close()

    return jsonify({
        "success": True,
        "lang": lang,

        "prediction_id": prediction_id,

        "location": location,

        "weather": {
            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "rainfall": weather["rainfall"],
        },

        "irrigation": {
            "needed": bool(today["irrigation"]),
            "water_today": today["water_today"],
            "alert": today["alert"],
            "alert_text": tr(today["alert"], lang),
        },

        # Codes are kept for existing clients; *_text fields are ready-to-show sentences in `lang`.
        "weather_alerts": today["weather_alerts"],
        "weather_alerts_text": [tr(irrigation_service.alert_message(c), lang) for c in today["weather_alerts"]],

        "recommendations": today["recommendations"],
        "recommendations_text": [tr(irrigation_service.recommendation_message(c), lang)
                                 for c in today["recommendations"]],

        "week_prediction": [dict(d, day_text=tr(d["day"], lang), irrigation_text=tr(d["irrigation"], lang))
                            for d in week],
    })
