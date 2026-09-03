from functools import wraps

from flask import redirect, request, session, url_for
from werkzeug.security import check_password_hash

from backend.models import AdminUser


def verify_admin(username: str, password: str) -> AdminUser | None:
    user = AdminUser.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped
