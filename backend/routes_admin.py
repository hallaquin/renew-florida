import csv
import io
import json
from pathlib import Path

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from backend.auth import login_required, verify_admin
from backend.crypto_utils import decrypt_text
from backend.extensions import db
from backend.models import CreditApplication

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

STATUS_OPTIONS = ["nueva", "revisada", "aprobada", "rechazada"]


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = verify_admin(username, password)
        if user:
            session.clear()
            session["admin_id"] = user.id
            session["admin_username"] = user.username
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        flash("Usuario o contraseña incorrectos.")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    status_filter = request.args.get("status", "")
    query = CreditApplication.query.order_by(CreditApplication.created_at.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)

    rows = []
    for record in query.all():
        data = json.loads(record.data_json)
        applicant = data.get("applicant", {})
        rows.append(
            {
                "id": record.id,
                "created_at": record.created_at,
                "status": record.status,
                "full_name": applicant.get("fullName", ""),
                "phone": applicant.get("phone", ""),
                "email": applicant.get("email", ""),
            }
        )

    return render_template(
        "admin/dashboard.html",
        rows=rows,
        status_filter=status_filter,
        status_options=STATUS_OPTIONS,
    )


@admin_bp.route("/credit-applications/<int:app_id>")
@login_required
def detail(app_id):
    record = CreditApplication.query.get_or_404(app_id)
    data = json.loads(record.data_json)
    return render_template(
        "admin/detail.html",
        record=record,
        data=data,
        status_options=STATUS_OPTIONS,
    )


@admin_bp.route("/credit-applications/<int:app_id>/reveal-ssn", methods=["POST"])
@login_required
def reveal_ssn(app_id):
    record = CreditApplication.query.get_or_404(app_id)
    return jsonify(
        {
            "ssn": decrypt_text(record.ssn_enc) or "",
            "coSsn": decrypt_text(record.co_ssn_enc) or "",
        }
    )


@admin_bp.route("/credit-applications/<int:app_id>/status", methods=["POST"])
@login_required
def update_status(app_id):
    record = CreditApplication.query.get_or_404(app_id)
    new_status = request.form.get("status", "nueva")
    if new_status in STATUS_OPTIONS:
        record.status = new_status
        db.session.commit()
        flash("Estatus actualizado.")
    return redirect(url_for("admin.detail", app_id=app_id))


def _safe_file_response(relative_path: str):
    upload_dir = Path(current_app.config["UPLOAD_DIR"]).resolve()
    target = (upload_dir / relative_path).resolve()
    if upload_dir not in target.parents:
        abort(404)
    if not target.exists():
        abort(404)
    return send_file(target)


@admin_bp.route("/credit-applications/<int:app_id>/id-photo")
@login_required
def id_photo(app_id):
    record = CreditApplication.query.get_or_404(app_id)
    if not record.id_photo_path:
        abort(404)
    return _safe_file_response(record.id_photo_path)


@admin_bp.route("/credit-applications/<int:app_id>/signature/<which>")
@login_required
def signature(app_id, which):
    record = CreditApplication.query.get_or_404(app_id)
    path = (
        record.signature_applicant_path
        if which == "applicant"
        else record.signature_coapplicant_path
    )
    if not path:
        abort(404)
    return _safe_file_response(path)


@admin_bp.route("/export.csv")
@login_required
def export_csv():
    applications = CreditApplication.query.order_by(CreditApplication.created_at.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "created_at", "status", "full_name", "phone", "email", "employer", "dealer"])
    for record in applications:
        data = json.loads(record.data_json)
        applicant = data.get("applicant", {})
        writer.writerow(
            [
                record.id,
                record.created_at.isoformat(),
                record.status,
                applicant.get("fullName", ""),
                applicant.get("phone", ""),
                applicant.get("email", ""),
                data.get("employment", {}).get("applicant", {}).get("employerName", ""),
                data.get("dealer", {}).get("repName", ""),
            ]
        )
    buffer.seek(0)
    return current_app.response_class(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=aplicaciones_credito.csv"},
    )
