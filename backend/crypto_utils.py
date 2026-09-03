import os

from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    key = os.environ.get("FERNET_KEY")
    if not key:
        raise RuntimeError(
            "Falta FERNET_KEY en el entorno. Genera una con: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt_text(plain: str | None) -> bytes | None:
    if not plain:
        return None
    return _get_fernet().encrypt(plain.encode())


def decrypt_text(token: bytes | None) -> str | None:
    if not token:
        return None
    return _get_fernet().decrypt(bytes(token)).decode()
