import hashlib
import hmac
import os
import time
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

_ITER = 310_000
_bearer = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, _ITER)
    return f"pbkdf2${_ITER}${salt.hex()}${dk.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, it, salt, dk = stored.split("$")
        new = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(it))
        return hmac.compare_digest(new.hex(), dk)
    except Exception:
        return False


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.token_minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.secret_key, algorithm="HS256")


def get_current_user(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(_bearer), db: Session = Depends(get_db)):
    from app.models import User

    token = creds.credentials if creds else request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        uid = int(jwt.decode(token, settings.secret_key, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "User not found")
    return user


_fails: dict[str, list[float]] = {}


def check_login_rate(key: str) -> None:
    now = time.time()
    _fails[key] = [t for t in _fails.get(key, []) if now - t < 900]
    if len(_fails[key]) >= 5:
        raise HTTPException(429, "Too many failed attempts. Try again in 15 minutes.")


def record_failure(key: str) -> None:
    _fails.setdefault(key, []).append(time.time())
