"""Crea (o resetea la contraseña de) el usuario administrador.

Uso:
    python -m backend.scripts.create_admin
"""

import getpass
import sys

from werkzeug.security import generate_password_hash

from backend.app import create_app
from backend.extensions import db
from backend.models import AdminUser


def main() -> None:
    app = create_app()
    with app.app_context():
        username = input("Usuario admin: ").strip()
        if not username:
            print("El usuario no puede estar vacío.")
            sys.exit(1)

        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirmar password: ")
        if not password or password != confirm:
            print("Los passwords no coinciden o están vacíos.")
            sys.exit(1)

        existing = AdminUser.query.filter_by(username=username).first()
        if existing:
            existing.password_hash = generate_password_hash(password)
            db.session.commit()
            print(f'Password actualizado para el admin "{username}".')
        else:
            user = AdminUser(username=username, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            print(f'Admin "{username}" creado.')


if __name__ == "__main__":
    main()
