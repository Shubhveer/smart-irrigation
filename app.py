import os
import logging

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from dotenv import load_dotenv

from database.db import init_db
from routes.farm_routes import farm_bp
from routes.predict_routes import predict_bp
from routes.api_routes import api_bp
from routes.farmer_extra_routes import farmer_extra
from routes.i18n_routes import i18n_bp
from services import i18n

load_dotenv()

logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)

    app.secret_key = os.getenv(
        "FLASK_SECRET_KEY",
        "dev-key-change-me"
    )

    # Reject uploads larger than 5 MB (image check / disease detection)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    # Initialize database
    init_db()

    # Register existing web routes
    app.register_blueprint(farm_bp)
    app.register_blueprint(predict_bp)

    # Register Farm Saathi mobile API routes
    app.register_blueprint(api_bp)

    # Register Farmer Extra routes
    app.register_blueprint(farmer_extra)

    # English / Hindi / Marathi (see services/i18n.py)
    app.register_blueprint(i18n_bp)
    i18n.init_app(app)

    @app.errorhandler(413)
    def too_large(_e):
        message = "The image is too large. Maximum size is 5 MB."
        if request.path.startswith("/api/"):
            return jsonify(error=i18n.tr(message)), 413
        flash(message)
        return redirect(url_for("farmer_extra.image_check"))

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", title="Page not found",
                               message="The page you are looking for does not exist."), 404

    @app.errorhandler(500)
    def server_error(_e):
        return render_template("error.html", title="Something went wrong",
                               message="An unexpected error occurred. Please try again."), 500

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = os.getenv(
        "FLASK_DEBUG",
        "false"
    ).lower() == "true"

    app.run(
        debug=debug_mode
    )