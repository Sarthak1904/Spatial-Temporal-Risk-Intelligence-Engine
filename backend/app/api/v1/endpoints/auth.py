"""Auth endpoints."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.security import create_access_token, verify_password
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth")
settings = get_settings()


@router.post("/token", response_model=TokenResponse)
def get_token(payload: TokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Issue JWT for valid credentials."""
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(
        subject=user.username,
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.jwt_expiration_minutes),
    )
    return TokenResponse(access_token=token)
