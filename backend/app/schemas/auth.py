"""Authentication request/response schemas."""

from pydantic import BaseModel


class TokenRequest(BaseModel):
    """Credential payload for login."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT response payload."""

    access_token: str
    token_type: str = "bearer"
