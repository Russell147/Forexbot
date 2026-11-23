from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (check_login_rate, create_token, get_current_user, hash_password, record_failure, verify_password)
from app.models import User
from app.schemas import Credentials

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
def register(body: Credentials, db: Session = Depends(get_db)):
    first = db.query(User).count() == 0
    if not first and not settings.allow_registration:
        raise HTTPException(403, "Registration is disabled")
    if db.query(User).filter_by(email=body.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    u = User(email=body.email.lower(), password_hash=hash_password(body.password), is_admin=first)
    db.add(u)
    db.commit()
    return {"id": u.id, "email": u.email}


@router.post("/login")
def login(body: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    key = f"{body.email.lower()}|{request.client.host if request.client else ''}"
    check_login_rate(key)
    u = db.query(User).filter_by(email=body.email.lower()).first()
    if not u or not verify_password(body.password, u.password_hash):
        record_failure(key)
        raise HTTPException(401, "Invalid email or password")
    token = create_token(u.id)
    response.set_cookie("access_token", token, httponly=True, secure=settings.cookie_secure,
                        samesite=settings.cookie_samesite, max_age=settings.token_minutes * 60)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "isAdmin": user.is_admin}
