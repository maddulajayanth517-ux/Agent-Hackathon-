import os

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import hash_password, issue_access_token, verify_password
from ..database import get_db
from ..models import User, UserRole
from ..rbac import get_current_user
from ..schemas import UserContext

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=12, max_length=256)


class PasswordSetRequest(LoginRequest):
    pass


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower(), User.is_active.is_(True)))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return {"access_token": issue_access_token(user.id, user.role.value), "token_type": "bearer", "user_id": user.id, "role": user.role.value}


@router.put("/password")
def set_password(payload: PasswordSetRequest, db: Session = Depends(get_db), user: UserContext = Depends(get_current_user)):
    account = db.scalar(select(User).where(User.id == user.id))
    account.password_hash = hash_password(payload.password)
    db.commit()
    return {"message": "Password updated"}


@router.post("/bootstrap-admin")
def bootstrap_admin(payload: PasswordSetRequest, x_bootstrap_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    configured = os.getenv("AUTH_BOOTSTRAP_TOKEN")
    if not configured or not x_bootstrap_token or not __import__("hmac").compare_digest(configured, x_bootstrap_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bootstrap authorization failed")
    account = db.scalar(select(User).where(User.email == payload.email.lower(), User.role == UserRole.ADMIN, User.is_active.is_(True)))
    if account is None:
        raise HTTPException(status_code=404, detail="Active administrator account not found")
    account.password_hash = hash_password(payload.password)
    db.commit()
    return {"message": "Administrator password initialized"}
