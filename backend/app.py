import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from backend.extensions import db, limiter
from backend.routes_admin import admin_bp
from backend.routes_api import api_bp

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")

    db_path = BASE_DIR / "data" / "renew_florida.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{db_path}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    upload_dir = BASE_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_DIR"] = str(upload_dir)

    # 10 MB máx. por request (fotos ID + firmas).
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

    db.init_app(app)
    limiter.init_app(app)

    # Admite uno o varios orígenes separados por coma, p. ej.:
    # "https://www.renewflorida.us,https://renewflorida.us"
    allowed_origins_raw = os.environ.get("CORS_ALLOWED_ORIGIN", "*")
    allowed_origins = (
        [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]
        if allowed_origins_raw != "*"
        else "*"
    )
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
