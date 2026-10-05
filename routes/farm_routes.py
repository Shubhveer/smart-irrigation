from flask import Blueprint, redirect, render_template, request, url_for

from routes._prg import recall, stash
from services.farm_advisory_service import (
    SYMPTOMS, CROP_OPTIONS, health_check, soil_review,
    fertilizer_plan, pest_review, farm_tasks
)

farm_bp = Blueprint("farm", __name__)

PEST_SYMPTOMS = [
    {"key": "holes", "name": "Holes or chewing on leaves"},
    {"key": "curling", "name": "Leaf curling or distortion"},
    {"key": "sticky", "name": "Sticky surface or black coating"},
    {"key": "wilting", "name": "Sudden wilting"},
    {"key": "spots", "name": "Spots or discolouration"},
    {"key": "insects", "name": "Visible insects"},
]


@farm_bp.route("/crop-health", methods=["GET", "POST"])
def crop_health():
    if request.method == "POST":
        stash("crop_health", health_check(
            request.form.get("crop", ""),
            request.form.get("stage", ""),
            request.form.getlist("symptoms"),
            request.form.get("notes", "")
        ))
        return redirect(url_for("farm.crop_health", r=1))
    return render_template("crop_health.html", symptoms=SYMPTOMS, result=recall("crop_health"))


@farm_bp.route("/soil", methods=["GET", "POST"])
def soil():
    if request.method == "POST":
        stash("soil", soil_review(request.form))
        return redirect(url_for("farm.soil", r=1))
    return render_template("soil.html", result=recall("soil"))


@farm_bp.route("/fertilizer", methods=["GET", "POST"])
def fertilizer():
    if request.method == "POST":
        stash("fertilizer", fertilizer_plan(request.form))
        return redirect(url_for("farm.fertilizer", r=1))
    return render_template("fertilizer.html", crops=CROP_OPTIONS, result=recall("fertilizer"))


@farm_bp.route("/pest", methods=["GET", "POST"])
def pest():
    if request.method == "POST":
        stash("pest", pest_review(request.form))
        return redirect(url_for("farm.pest", r=1))
    return render_template("pest.html", crops=CROP_OPTIONS, symptoms=PEST_SYMPTOMS, result=recall("pest"))


@farm_bp.route("/farm-plan")
def farm_plan():
    return render_template("farm_plan.html", tasks=farm_tasks())
