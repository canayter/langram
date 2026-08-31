"""Password hashing and the two kinds of token this app signs.

Access tokens identify a learner. Item tokens carry the specification of an
exercise item that has been served, so the server can derive the answer again on
submission without keeping session state and without ever sending the answer to
the browser.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from .config import get_settings

_hasher = PasswordHasher()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return _hasher.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except InvalidHashError:
        return False


def _encode(claims: dict[str, Any], minutes: float) -> str:
    settings = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    payload = {**claims, "iat": now, "exp": now + dt.timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.resolved_secret(), algorithm=ALGORITHM)


def _decode(token: str, expected: str) -> dict[str, Any]:
    settings = get_settings()
    payload = jwt.decode(token, settings.resolved_secret(), algorithms=[ALGORITHM])
    if payload.get("kind") != expected:
        raise jwt.InvalidTokenError(f"expected a {expected} token")
    return payload


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    return _encode({"sub": str(user_id), "kind": "access"}, settings.access_token_hours * 60)


def read_access_token(token: str) -> int:
    return int(_decode(token, "access")["sub"])


def create_item_token(spec: dict[str, Any]) -> str:
    settings = get_settings()
    return _encode({"kind": "item", "spec": spec}, settings.item_token_minutes)


def read_item_token(token: str) -> dict[str, Any]:
    return _decode(token, "item")["spec"]
