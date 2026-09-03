from datetime import datetime

from backend.extensions import db


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class CreditApplication(db.Model):
    __tablename__ = "credit_applications"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="nueva", nullable=False)

    # Campos no sensibles (nombre, contacto, empleo, dealer, etc.) agrupados como JSON.
    # Ver backend/README.md para la forma exacta de este objeto.
    data_json = db.Column(db.Text, nullable=False)

    # SSN cifrado con Fernet (backend/crypto_utils.py). Nunca se guarda en texto plano.
    ssn_enc = db.Column(db.LargeBinary, nullable=True)
    co_ssn_enc = db.Column(db.LargeBinary, nullable=True)

    id_photo_path = db.Column(db.String(255), nullable=True)
    signature_applicant_path = db.Column(db.String(255), nullable=True)
    signature_coapplicant_path = db.Column(db.String(255), nullable=True)
