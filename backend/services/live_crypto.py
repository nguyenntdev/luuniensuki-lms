"""Encryption and redaction helpers for live AI session data."""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from ..config import settings


def _derive_key(seed: str) -> bytes:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    raw = (
        getattr(settings, "live_data_encryption_key", None)
        or settings.jwt_secret_key
        or "luuniensuki-live-default-key"
    )
    seed = str(raw).strip() or "luuniensuki-live-default-key"
    try:
        return Fernet(seed.encode("utf-8"))
    except Exception:
        # If not a valid Fernet key, derive one deterministically.
        return Fernet(_derive_key(seed))


def encrypt_text(value: str) -> str:
    plaintext = str(value or "")
    token = _fernet().encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(value: str | None) -> str:
    if not value:
        return ""
    token = str(value).encode("utf-8")
    try:
        return _fernet().decrypt(token).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeDecodeError):
        # Backward compatibility for plain text rows.
        return str(value)


def redact_text(value: str, *, max_len: int = 120) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    if len(text) <= 8:
        return "[redacted]"
    head = text[:4]
    tail = text[-2:]
    core = "*" * min(24, max(4, len(text) - 6))
    compact = f"{head}{core}{tail}"
    if len(compact) > max_len:
        return compact[: max_len - 3] + "..."
    return compact
