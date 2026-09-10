"""Passwordless mock auth. Email in, JWT with tenant claims out.

This stands in for OIDC / magic-link. It is intentionally not a real IdP.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app import config
from app.store import Store, get_store

_bearer = HTTPBearer(auto_error=False)


def issue_token(user: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    perms = sorted(config.ROLE_PERMS.get(user["role"], config.ROLE_PERMS["viewer"]))
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "name": user["name"],
        "tenant_id": user["tenant_id"],
        "role": user["role"],
        "perms": perms,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=config.JWT_TTL_SECONDS)).timestamp()),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def current_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    store: Store = Depends(get_store),
) -> dict[str, Any]:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")
    claims = decode_token(creds.credentials)
    user = store.get_user(claims.get("sub", ""))
    if user is None or user["tenant_id"] != claims.get("tenant_id"):
        raise HTTPException(status_code=401, detail="Unknown principal")
    return {
        "user": user,
        "tenant_id": user["tenant_id"],
        "role": user["role"],
        "perms": set(claims.get("perms") or []),
        "claims": claims,
    }


def require_perm(perm: str):
    def _dep(principal: dict[str, Any] = Depends(current_principal)) -> dict[str, Any]:
        if perm not in principal["perms"]:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{principal['role']}' is missing permission '{perm}'",
            )
        return principal

    return _dep


def idempotency_key(idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key")) -> str | None:
    if idempotency_key_header is not None and not idempotency_key_header.strip():
        raise HTTPException(status_code=400, detail="Idempotency-Key must be non-empty when provided")
    return idempotency_key_header
