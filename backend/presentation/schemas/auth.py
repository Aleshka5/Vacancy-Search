"""Pydantic schemas for auth endpoints."""

from pydantic import BaseModel, EmailStr, Field


class GoogleAuthRequest(BaseModel):
    """Request body for POST /auth/google."""

    id_token: EmailStr
    redirect_uri: str = "https://vacancy-search.app/callback"


class GoogleAuthResponse(BaseModel):
    """Response body for POST /auth/google."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900


class RefreshRequest(BaseModel):
    """Request body for POST /auth/refresh."""

    refresh_token: str = Field(description="Refresh token from cookie or body.")


class RefreshResponse(BaseModel):
    """Response body for POST /auth/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900
