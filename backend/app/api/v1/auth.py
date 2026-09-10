from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel
from typing import Set, Tuple, Annotated, Optional

from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, User as UserSchema, Token
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    decode_access_token,
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

_TOKEN_BLACKLIST: Set[Tuple[str, datetime]] = set()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _blacklist_cleanup():
    now = _now_utc()
    expired = {t for t in _TOKEN_BLACKLIST if t[1] <= now}
    for e in expired:
        _TOKEN_BLACKLIST.discard(e)


def is_token_blacklisted(jti_or_token: str) -> bool:
    _blacklist_cleanup()
    return any(t[0] == jti_or_token for t in _TOKEN_BLACKLIST)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user: UserSchema


@router.post("/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=TokenWithUser)
def login(form_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/login/oauth", response_model=Token)
def login_oauth(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_active_user),
    authorization: Optional[str] = Header(default=None),
):
    raw_token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        raw_token = authorization.split(" ", 1)[1].strip()

    exp_dt = _now_utc() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    if raw_token:
        _TOKEN_BLACKLIST.add((raw_token, exp_dt))
    _blacklist_cleanup()
    return {
        "success": True,
        "message": "Logged out successfully",
        "user": current_user.email,
    }
