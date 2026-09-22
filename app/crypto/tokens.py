"""Criptografia de access tokens (Fernet derivado de TOKEN_ENCRYPTION_KEY)."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


def _fernet() -> Fernet:
    secret = get_settings().token_encryption_key
    if not secret:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY nao configurado")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_token(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_token(blob: str) -> str:
    try:
        return _fernet().decrypt(blob.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Falha ao descriptografar token") from exc
