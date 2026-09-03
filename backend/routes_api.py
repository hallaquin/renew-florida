import json
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from backend.crypto_utils import encrypt_text
from backend.extensions import db, limiter
from backend.models import CreditApplication

api_bp = Blueprint("api", __name__, url_prefix="/api")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

REQUIRED_FIELDS = [
    "fullName",
    "dateOfBirth",
    "ssn",
    "dlNumber",
    "dlState",
    "phone",
    "email",
    "address",
    "dealerName",
]


def _field(name: str, default: str = "") -> str:
    return request.form.get(name, default).strip()


def _save_upload(file_storage, dest_path: Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    file_storage.save(dest_path)


def _applicant_payload(prefix: str = "") -> dict:
    p = f"{prefix}_" if prefix else ""
    return {
        "amount": _field(f"{p}amount"),
        "fullName": _field(f"{p}fullName"),
        "dateOfBirth": _field(f"{p}dateOfBirth"),
        "driversLicense": {
            "number": _field(f"{p}dlNumber"),
            "state": _field(f"{p}dlState"),
            "issueDate": _field(f"{p}dlIssueDate"),
            "expDate": _field(f"{p}dlExpDate"),
        },
        "phone": _field(f"{p}phone"),
        "email": _field(f"{p}email"),
        "address": _field(f"{p}address"),
        "timeLivingAtAddress": _field(f"{p}timeLiving"),
        "monthlyMortgageOrRent": _field(f"{p}mortgagePayment"),
        "housingType": _field(f"{p}housingType"),
        "housingStatus": _field(f"{p}housingStatus"),
    }


def _employment_payload(prefix: str) -> dict:
    p = f"{prefix}_"
    return {
        "incomeType": _field(f"{p}incomeType"),
        "employerName": _field(f"{p}employerName"),
        "workPhone": _field(f"{p}workPhone"),
        "workAddress": _field(f"{p}workAddress"),
        "role": _field(f"{p}role"),
        "timeOnJob": _field(f"{p}timeOnJob"),
        "monthlyIncome": _field(f"{p}monthlyIncome"),
        "incomeFrequency": _field(f"{p}incomeFrequency"),
    }


@api_bp.route("/credit-applications", methods=["POST"])
@limiter.limit("5 per hour")
def create_credit_application():
    missing = [f for f in REQUIRED_FIELDS if not _field(f)]

    id_photo = request.files.get("idPhoto")
    signature_applicant = request.files.get("signatureApplicant")

    if not id_photo or id_photo.filename == "":
        missing.append("idPhoto")
    elif id_photo.mimetype not in ALLOWED_IMAGE_TYPES:
        return jsonify({"error": "La foto de identificación debe ser una imagen JPEG, PNG o WEBP."}), 400

    if not signature_applicant or signature_applicant.filename == "":
        missing.append("signatureApplicant")

    if missing:
        return jsonify({"error": "Faltan campos obligatorios.", "fields": missing}), 400

    co_applicant = _applicant_payload("co")
    has_co_applicant = bool(co_applicant["fullName"])

    data = {
        "applicant": _applicant_payload(),
        "coApplicant": co_applicant if has_co_applicant else None,
        "employment": {
            "applicant": _employment_payload("emp"),
            "coApplicant": _employment_payload("coEmp") if has_co_applicant else None,
        },
        "dealer": {"repName": _field("dealerName")},
    }

    co_ssn = _field("co_ssn")

    record = CreditApplication(
        status="nueva",
        data_json=json.dumps(data, ensure_ascii=False),
        ssn_enc=encrypt_text(_field("ssn")),
        co_ssn_enc=encrypt_text(co_ssn) if co_ssn else None,
    )
    db.session.add(record)
    db.session.commit()

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    record_dir = upload_dir / "credit" / str(record.id)

    id_photo_ext = Path(secure_filename(id_photo.filename)).suffix or ".jpg"
    id_photo_dest = record_dir / f"id_photo{id_photo_ext}"
    _save_upload(id_photo, id_photo_dest)
    record.id_photo_path = str(id_photo_dest.relative_to(upload_dir))

    signature_applicant_dest = record_dir / "signature_applicant.png"
    _save_upload(signature_applicant, signature_applicant_dest)
    record.signature_applicant_path = str(signature_applicant_dest.relative_to(upload_dir))

    signature_co_applicant = request.files.get("signatureCoApplicant")
    if signature_co_applicant and signature_co_applicant.filename:
        signature_co_dest = record_dir / "signature_coapplicant.png"
        _save_upload(signature_co_applicant, signature_co_dest)
        record.signature_coapplicant_path = str(signature_co_dest.relative_to(upload_dir))

    db.session.commit()

    return jsonify({"id": record.id, "status": "ok"}), 201
