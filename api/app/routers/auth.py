from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_current_user
from app.models import RefreshToken, User
from app.schemas import AccessToken, LoginRequest, RegisterRequest, UserRead
from app.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/auth",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


def _issue_tokens(user: User, db: Session, response: Response) -> AccessToken:
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    db.commit()

    _set_refresh_cookie(response, refresh_token)
    return AccessToken(access_token=access_token)


@router.post("/register", response_model=AccessToken, status_code=201)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> AccessToken:
    existing = db.scalar(select(User).where(User.email == body.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="an account with this email already exists")

    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_tokens(user, db, response)


@router.post("/login", response_model=AccessToken)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AccessToken:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="invalid email or password")

    return _issue_tokens(user, db, response)


@router.post("/refresh", response_model=AccessToken)
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
) -> AccessToken:
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="no refresh token")

    try:
        user_id = decode_token(refresh_token, expected_type="refresh")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid or expired refresh token")

    token_hash = hash_token(refresh_token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    now = datetime.now(timezone.utc)
    if stored is None or stored.revoked or stored.expires_at < now:
        raise HTTPException(status_code=401, detail="invalid or expired refresh token")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="user not found")

    # rotate: the presented refresh token is single-use
    stored.revoked = True
    db.commit()

    return _issue_tokens(user, db, response)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
) -> None:
    if refresh_token is not None:
        token_hash = hash_token(refresh_token)
        stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        if stored is not None:
            stored.revoked = True
            db.commit()

    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/auth")


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
