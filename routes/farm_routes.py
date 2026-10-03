from flask import Blueprint, render_template, request

from services.farm_advisory_service import (
    SYMPTOMS, CROP_OPTIONS, health_check, soil_review,
    fertilizer_plan, pest_review, farm_tasks
)

farm_bp = Blueprint("farm", __name__)

@farm_bp.route("/crop-health", methods=["GET", "POST"])
def crop_health():
    result = None
    if request.method == "POST":
        result = health_check(
            request.form.get("crop", ""),
            request.form.get("stage", ""),
            request.form.getlist("symptoms"),
            request.form.get("notes", "")
        )
    return render_template("crop_health.html", symptoms=SYMPTOMS, result=result)

@farm_bp.route("/soil", methods=["GET", "POST"])
def soil():
    result = None
    if request.method == "POST":
        result = soil_review(request.form)
    return render_template("soil.html", result=result)

@farm_bp.route("/fertilizer", methods=["GET", "POST"])
def fertilizer():
    result = None
    if request.method == "POST":
        result = fertilizer_plan(request.form)
    return render_template("fertilizer.html", crops=CROP_OPTIONS, result=result)

@farm_bp.route("/pest", methods=["GET", "POST"])
def pest():
    result = None
    if request.method == "POST":
        result = pest_review(request.form)
    pest_symptoms = [
        {"key":"holes","name":"Holes or chewing on leaves"},
        {"key":"curling","name":"Leaf curling or distortion"},
        {"key":"sticky","name":"Sticky surface or black coating"},
        {"key":"wilting","name":"Sudden wilting"},
        {"key":"spots","name":"Spots or discolouration"},
        {"key":"insects","name":"Visible insects"}
    ]
    return render_template("pest.html", crops=CROP_OPTIONS, symptoms=pest_symptoms, result=result)

@farm_bp.route("/farm-plan")
def farm_plan():
    return render_template("farm_plan.html", tasks=farm_tasks())
