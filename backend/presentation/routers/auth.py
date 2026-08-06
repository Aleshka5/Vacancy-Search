"""Auth router — /api/v1/auth endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from starlette.responses import Response as StarletteResponse

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
    redirect_uri: str = "https://vacancy-search.app/callback"


class GoogleAuthResponse(BaseModel):
    """Response body for Google OAuth login."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900
    user: User


class RefreshResponse(BaseModel):
    """Response body for POST /auth/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------


class DummySession:
    """Placeholder session for use inside dependency functions."""
    pass


def _get_google_oauth_use_case() -> GoogleOAuthUseCase:
    from backend.infrastructure.repositories.postgres_user_repository import (
        PostgresUserRepository,
    )
    from backend.config.settings import settings

    jwt_handler = JWTHandler(settings)
    google_handler = GoogleOAuthHandler(
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
    )
    refresh_use_case = RefreshTokenUseCase(jwt_handler)
    user_repo = PostgresUserRepository(DummySession())
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
)
async def google_auth(
    request: GoogleAuthRequest,
    use_case: Annotated[GoogleOAuthUseCase, Depends(_get_google_oauth_use_case)],
    response=Depends(),
):
    result = await use_case.authenticate(request.id_token)
    user = result["user"]

    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=30 * 24 * 60 * 60,
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
)
async def refresh(
    request: Annotated[RefreshTokenUseCase, Depends(_get_refresh_use_case)],
    refresh_token: str | None = Depends(lambda r: r.cookies.get("refresh_token")),
    response=Depends(),
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
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user
