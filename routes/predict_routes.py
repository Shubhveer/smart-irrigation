import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file

from database.db import SessionLocal
from database.models import Prediction
from services import weather_service, irrigation_service, report_service
from services.i18n import M, get_lang

logger = logging.getLogger(__name__)
predict_bp = Blueprint("predict", __name__)


@predict_bp.route("/")
def index():
    return render_template("index.html")


@predict_bp.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return redirect(url_for("predict.index"))

    location = request.form.get("location", "").strip()
    soil_raw = request.form.get("soil_type")
    stage_raw = request.form.get("crop_stage")
    size_raw = request.form.get("field_size")

    if not location or soil_raw is None or stage_raw is None:
        flash("Please fill in location, soil type, and crop stage.")
        return redirect(url_for("predict.index"))

    try:
        soil = int(soil_raw)
        stage = int(stage_raw)
        field_size = float(size_raw) if size_raw else 1.0
    except ValueError:
        flash("Soil type and crop stage must be numbers.")
        return redirect(url_for("predict.index"))

    try:
        weather = weather_service.get_weather(location)
        forecast_data = weather_service.get_forecast(location)
    except weather_service.WeatherServiceError as e:
        logger.warning("Weather lookup failed: %s", e)
        flash(M("Couldn't fetch weather for '{location}'. Check the spelling and try again.", location=location))
        return redirect(url_for("predict.index"))

    today = irrigation_service.build_today_result(
        weather["temperature"], weather["humidity"], weather["rainfall"], soil, stage, field_size
    )
    week = irrigation_service.build_week_prediction(forecast_data, soil, stage, field_size)

    db = SessionLocal()
    try:
        record = Prediction(
            location=location, soil_type=soil, crop_stage=stage, field_size=field_size,
            temperature=weather["temperature"], humidity=weather["humidity"], rainfall=weather["rainfall"],
            alert=today["alert"], water_today=today["water_today"],
            weather_alerts=today["weather_alerts"], recommendations=today["recommendations"],
            week_prediction=week,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        prediction_id = record.id
    finally:
        db.close()

    return redirect(url_for("predict.result", prediction_id=prediction_id))


@predict_bp.route("/result/<int:prediction_id>")
def result(prediction_id):
    """Saved result page. Because it is a normal GET page, the language can be switched on it."""
    db = SessionLocal()
    try:
        r = db.get(Prediction, prediction_id)
        if not r:
            flash("Report not found.")
            return redirect(url_for("predict.index"))
        ctx = dict(
            location=r.location, temperature=r.temperature, humidity=r.humidity, rainfall=r.rainfall,
            alert=r.alert, irrigation_needed=(r.alert == "Irrigation Required"), water_needed=r.water_today,
            week_prediction=r.week_prediction or [], weather_alerts=r.weather_alerts or [],
            recommendations=r.recommendations or [], prediction_id=r.id,
        )
    finally:
        db.close()
    return render_template(
        "result.html", **ctx,
        alert_messages=[irrigation_service.alert_message(c) for c in ctx["weather_alerts"]],
        recommendation_messages=[irrigation_service.recommendation_message(c) for c in ctx["recommendations"]],
    )


@predict_bp.route("/download/<int:prediction_id>")
def download(prediction_id):
    db = SessionLocal()
    try:
        record = db.get(Prediction, prediction_id)
        if not record:
            flash("Report not found.")
            return redirect(url_for("predict.index"))
        file_path = report_service.build_excel_report(record, get_lang())
    finally:
        db.close()
    return send_file(file_path, as_attachment=True)


@predict_bp.route("/history")
def history():
    db = SessionLocal()
    try:
        records = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(50).all()
        history_data = [r.to_dict() for r in records]
    finally:
        db.close()
    return render_template("history.html", history=history_data)
