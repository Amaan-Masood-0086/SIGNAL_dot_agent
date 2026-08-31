"""JWT (RS256) token helpers — FEAT-01 auth stub.

RS256 per sdlc-security.md OWASP A02. `institution_id` and `role` are
embedded as signed claims (TRD §4 security controls). This is a STUB — real
credential verification, account lockout, and token blacklisting arrive in
FEAT-12.
"""

from __future__ import annotations

import datetime
import uuid

import jwt

from .config import get_settings

ALGORITHM = "RS256"
ALLOWED_ROLES = {"caretaker", "admin"}


def create_access_token(
    *,
    staff_id: str,
    institution_id: str,
    role: str,
    private_key_pem: str | None = None,
    expires_minutes: int | None = None,
    issuer: str | None = None,
    settings=None,
) -> str:
    settings = settings or get_settings()
    now = datetime.datetime.now(datetime.timezone.utc)
    claims = {
        "sub": staff_id,
        "institution_id": institution_id,
        "role": role,
        "iss": issuer or settings.JWT_ISSUER,
        "iat": now,
        "exp": now
        + datetime.timedelta(
            minutes=expires_minutes
            if expires_minutes is not None
            else settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        ),
        "jti": str(uuid.uuid4()),
    }
    key = private_key_pem if private_key_pem is not None else settings.JWT_PRIVATE_KEY
    return jwt.encode(claims, key, algorithm=ALGORITHM)


def decode_access_token(token: str, *, settings=None) -> dict:
    """Verify signature + expiry + issuer against the configured public key.

    Raises jwt.PyJWTError on any failure — callers map that to 401.
    """
    settings = settings or get_settings()
    return jwt.decode(
        token,
        settings.JWT_PUBLIC_KEY,
        algorithms=[ALGORITHM],
        issuer=settings.JWT_ISSUER,
    )
