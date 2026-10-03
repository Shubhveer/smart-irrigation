import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from database.db import SessionLocal
from database.models import Prediction
from services import weather_service, irrigation_service, report_service
logger=logging.getLogger(__name__); predict_bp=Blueprint("predict",__name__)
@predict_bp.route("/")
def index(): return render_template("index.html")
@predict_bp.route("/predict",methods=["GET","POST"])
def predict():
    if request.method=="GET": return redirect(url_for("predict.index"))
    location=request.form.get("location","").strip(); crop=request.form.get("crop","Wheat").strip(); soil=request.form.get("soil_type","Black Soil").strip(); stage=request.form.get("crop_stage","Germination").strip(); moi_raw=request.form.get("moi"); size_raw=request.form.get("field_size")
    if not location or not crop or not soil or not stage or moi_raw is None: flash("Please fill in location, crop, soil type, crop stage and soil moisture."); return redirect(url_for("predict.index"))
    try: moi=float(moi_raw); field_size=float(size_raw) if size_raw else 1.0
    except ValueError: flash("Soil moisture and field size must be numbers."); return redirect(url_for("predict.index"))
    try: weather=weather_service.get_weather(location); forecast_data=weather_service.get_forecast(location)
    except weather_service.WeatherServiceError as e: logger.warning("Weather lookup failed: %s",e); flash(f"Could not fetch weather for {location}."); return redirect(url_for("predict.index"))
    try: today=irrigation_service.build_today_result(crop,soil,stage,moi,weather["temperature"],weather["humidity"],field_size); week=irrigation_service.build_week_prediction(forecast_data,crop,soil,stage,moi,field_size)
    except RuntimeError as e: flash(str(e)); return redirect(url_for("predict.index"))
    db=SessionLocal()
    try:
        record=Prediction(location=location,soil_type=soil,crop_stage=stage,field_size=field_size,temperature=weather["temperature"],humidity=weather["humidity"],rainfall=weather["rainfall"],alert=today["alert"],water_today=today["water_today"],weather_alerts=today["weather_alerts"],recommendations=today["recommendations"],week_prediction=week)
        db.add(record); db.commit(); db.refresh(record); prediction_id=record.id
    finally: db.close()
    return render_template("result.html",location=location,temperature=weather["temperature"],humidity=weather["humidity"],rainfall=weather["rainfall"],alert=today["alert"],irrigation_needed=today["irrigation"]==1,water_needed=today["water_today"],week_prediction=week,weather_alerts=today["weather_alerts"],recommendations=today["recommendations"],prediction_id=prediction_id)
@predict_bp.route("/download/<int:prediction_id>")
def download(prediction_id):
    db=SessionLocal()
    try:
        record=db.get(Prediction,prediction_id)
        if not record: flash("Report not found."); return redirect(url_for("predict.index"))
        file_path=report_service.build_excel_report(record)
    finally: db.close()
    return send_file(file_path,as_attachment=True)
@predict_bp.route("/history")
def history():
    db=SessionLocal()
    try: records=db.query(Prediction).order_by(Prediction.created_at.desc()).limit(50).all(); history_data=[r.to_dict() for r in records]
    finally: db.close()
    return render_template("history.html",history=history_data)