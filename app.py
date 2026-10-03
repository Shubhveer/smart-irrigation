import os
import logging

from flask import Flask
from dotenv import load_dotenv

from database.db import init_db
from routes.farm_routes import farm_bp
from routes.predict_routes import predict_bp
from routes.api_routes import api_bp
from routes.farmer_extra_routes import farmer_extra

load_dotenv()

logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)

    app.secret_key = os.getenv(
        "FLASK_SECRET_KEY",
        "dev-key-change-me"
    )

    # Initialize database
    init_db()

    # Register existing web routes
    app.register_blueprint(farm_bp)
    app.register_blueprint(predict_bp)

    # Register Farm Saathi mobile API routes
    app.register_blueprint(api_bp)

    # Register Farmer Extra routes
    app.register_blueprint(farmer_extra)

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