from flask import Blueprint, render_template, request, flash
from services.government_news import get_official_sources
from services.image_screening_service import screen_image

farmer_extra = Blueprint("farmer_extra", __name__)

@farmer_extra.get("/government-news")
def government_news():
    return render_template("government_news.html", news_items=get_official_sources())

@farmer_extra.route("/image-check", methods=["GET", "POST"])
def image_check():
    result = None
    if request.method == "POST":
        image = request.files.get("image")
        mode = request.form.get("mode", "plant")
        if not image or not image.filename:
            flash("Please choose a JPG image.")
        elif not image.filename.lower().endswith((".jpg", ".jpeg")):
            flash("Only JPG/JPEG images are accepted.")
        else:
            try:
                result = screen_image(image, mode)
            except Exception:
                flash("The image could not be processed. Please use a valid JPG/JPEG file.")
    return render_template("image_check.html", result=result)
