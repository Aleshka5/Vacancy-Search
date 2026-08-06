"""Auth router — /api/v1/auth endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field

from backend.application.use_cases.google_oauth import GoogleOAuthUseCase
from backend.application.use_cases.refresh_token import RefreshTokenUseCase
from backend.domain.entities.user import User
from backend.domain.interfaces.i_user_repository import IUserRepository
from backend.domain.value_objects.role import Role
from backend.infrastructure.auth.google_oauth import GoogleOAuthHandler
from backend.infrastructure.auth.jwt_handler import JWTHandler
from backend.presentation.dependencies import get_current_user, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------


class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth login."""

    id_token: EmailStr = Field(
        description="Google ID token (JWT), not the OAuth authorization code.",
    )
    redirect_uri: str = "https://vacancy-search.app/callback"  # configurable


class GoogleAuthResponse(BaseModel):
    """Response body for Google OAuth login."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900  # 15 minutes
    user: User


class RefreshResponse(BaseModel):
    """Response body for token refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------


def _get_google_oauth_use_case() -> GoogleOAuthUseCase:
    from backend.infrastructure.repositories.postgres_user_repository import (
        PostgresUserRepository,
    )

    # Create handler instances with settings
    from backend.config.settings import settings

    jwt_handler = JWTHandler(settings)
    google_handler = GoogleOAuthHandler(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    refresh_use_case = RefreshTokenUseCase(jwt_handler)

    # We'll use a placeholder session — the router receives it via FastAPI deps
    class _DummySession:
        pass

    user_repo = PostgresUserRepository(_DummySession())
    return GoogleOAuthUseCase(user_repo, jwt_handler, google_handler, refresh_use_case)


def _get_refresh_use_case() -> RefreshTokenUseCase:
    from backend.config.settings import settings

    jwt_handler = JWTHandler(settings)
    return RefreshTokenUseCase(jwt_handler)


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post(
    "/google",
    response_model=GoogleAuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Exchange Google ID token for JWT",
    description="""
    POST /api/v1/auth/google

    Accepts a Google ID token and returns access + refresh JWTs.
    - Access Token (15 min) — returned in JSON body for frontend memory storage.
    - Refresh Token (30 days) — set as HttpOnly, Secure, SameSite=Strict cookie.
    """,
)
async def google_auth(
    request: GoogleAuthRequest,
    use_case: Annotated[GoogleOAuthUseCase, Depends(_get_google_oauth_use_case)],
    response: Response,
):
    result = await use_case.authenticate(request.id_token)
    user = result["user"]

    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=30 * 24 * 60 * 60,  # 30 days
        path="/api/v1/auth/refresh",
    )

    return GoogleAuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user=user,
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using refresh cookie",
    description="""
    POST /api/v1/auth/refresh

    Expects the refresh_token cookie. Returns a new access token and
    a rotated refresh token (set as cookie).
    """,
)
async def refresh(
    request: RefreshTokenUseCase = Depends(_get_refresh_use_case),
    refresh_token: str | None = Depends(lambda r: r.cookies.get("refresh_token")),
    response: Response = Depends(),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    try:
        result = await request.refresh(refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Set new refresh token as cookie (rotation)
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=30 * 24 * 60 * 60,
        path="/api/v1/auth/refresh",
    )

    return RefreshResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )


@router.get(
    "/me",
    response_model=User,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Returns the authenticated user's profile.",
)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user
