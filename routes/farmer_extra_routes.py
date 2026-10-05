from flask import Blueprint, redirect, render_template, request, flash, jsonify, url_for

from routes._prg import recall, stash
from services.government_news import get_official_sources
from services.i18n import get_lang, tr
from services.image_screening_service import screen_image

farmer_extra = Blueprint("farmer_extra", __name__)


@farmer_extra.get("/government-news")
def government_news():
    return render_template("government_news.html", news_items=get_official_sources())


@farmer_extra.route("/image-check", methods=["GET", "POST"])
def image_check():
    if request.method == "POST":
        image = request.files.get("image")
        mode = request.form.get("mode", "plant")
        if not image or not image.filename:
            flash("Please choose a JPG image.")
        elif not image.filename.lower().endswith((".jpg", ".jpeg")):
            flash("Only JPG/JPEG images are accepted.")
        else:
            try:
                stash("image", screen_image(image, mode))
                return redirect(url_for("farmer_extra.image_check", r=1))
            except Exception:
                flash("The image could not be processed. Please use a valid JPG/JPEG file.")
    return render_template("image_check.html", result=recall("image"))


def image_result_json(result, lang):
    """Machine-readable fields stay as they were; text fields are translated for the app."""
    preds = [dict(p, plant_text=tr(p["plant"], lang), disease_text=tr(p["disease"], lang))
             for p in result.get("top_predictions", [])]
    return {"lang": lang, "confident": result.get("confident"), "top_predictions": preds,
            "finding": tr(result["finding"], lang),
            "recommendation": " ".join(tr(result["recommendation"], lang))}


@farmer_extra.post("/api/disease-detect")
def disease_detect_api():
    """JSON endpoint for the mobile app: multipart field 'image' (JPG). Language: ?lang=hi|mr|en or Accept-Language."""
    lang = get_lang()
    image = request.files.get("image")
    if not image or not image.filename.lower().endswith((".jpg", ".jpeg")):
        return jsonify(error=tr("Upload a JPG image under 5 MB", lang)), 400
    try:
        return jsonify(image_result_json(screen_image(image, "plant"), lang))
    except Exception:
        return jsonify(error=tr("Invalid image", lang)), 400
