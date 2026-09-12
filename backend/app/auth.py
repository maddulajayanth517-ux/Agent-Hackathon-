"""Small dependency-free password and signed access-token implementation."""
import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$" + base64.urlsafe_b64encode(salt + digest).decode()


def verify_password(password: str, stored: str | None) -> bool:
    if not stored or not stored.startswith("scrypt$"):
        return False
    try:
        raw = base64.urlsafe_b64decode(stored.split("$", 1)[1].encode())
        salt, expected = raw[:16], raw[16:]
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _secret() -> bytes:
    value = os.getenv("AUTH_SECRET")
    if not value:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AUTH_SECRET is not configured")
    return value.encode()


def issue_access_token(user_id: int, role: str, minutes: int = 480) -> str:
    payload = {"sub": user_id, "role": role, "exp": int((datetime.now(timezone.utc) + timedelta(minutes=minutes)).timestamp())}
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).rstrip(b"=")
    signature = hmac.new(_secret(), encoded, hashlib.sha256).digest()
    return encoded.decode() + "." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()


def verify_access_token(token: str) -> dict:
    try:
        payload_part, signature_part = token.split(".", 1)
        encoded = payload_part.encode()
        expected = hmac.new(_secret(), encoded, hashlib.sha256).digest()
        actual = base64.urlsafe_b64decode(signature_part + "=" * (-len(signature_part) % 4))
        payload = json.loads(base64.urlsafe_b64decode(payload_part + "=" * (-len(payload_part) % 4)))
        if not hmac.compare_digest(expected, actual) or int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            raise ValueError
        return payload
    except (ValueError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")
