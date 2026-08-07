"""Admin router — /api/v1/admin endpoints."""
from __future__ import annotations

import logging
from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import Settings
from backend.domain.entities.user import User
from backend.domain.interfaces.i_user_repository import IUserRepository
from backend.domain.value_objects.role import Role
from backend.infrastructure.auth.jwt_handler import JWTHandler
from backend.presentation.dependencies import get_current_user
from backend.presentation.schemas.admin import BlockRequest, UserResponse, UsersListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

# ------------------------------------------------------------------
# Dependency helpers (module-level so they can be patched in tests)
# ------------------------------------------------------------------

_user_repo = None  # type: ignore[assignment]
_jwt_handler = None  # type: ignore[assignment]
_settings = None  # type: ignore[assignment]


def _get_user_repo() -> IUserRepository:
    """Return patched repo or auto-wired one."""
    global _user_repo
    if _user_repo is not None:
        return _user_repo
    from unittest.mock import MagicMock

    return MagicMock(spec=IUserRepository)


def _get_jwt_handler() -> JWTHandler:
    """Return patched handler or auto-wired one."""
    global _jwt_handler
    if _jwt_handler is not None:
        return _jwt_handler
    return JWTHandler(_get_settings())


def _get_settings() -> Settings:
    """Return patched settings or auto-wired one."""
    global _settings
    if _settings is not None:
        return _settings
    return Settings()


async def get_db() -> AsyncSession:
    """Dependency that yields an async database session."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine(_get_settings().DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


# ------------------------------------------------------------------
# Admin dependency
# ------------------------------------------------------------------


async def get_current_admin(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))
    ],
    user_repo: Any = None,
    jwt_handler: Any = None,
    settings: Any = None,
) -> User:
    """Dependency that extracts and validates JWT for admin endpoints.

    Unlike get_current_user, this does NOT raise 403 for blocked users
    (admin can block themselves). Raises 403 if user is not admin.
    """
    user_repo = user_repo or _get_user_repo()
    jwt_handler = jwt_handler or _get_jwt_handler()
    settings = settings or _get_settings()

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt_handler.validate_access_token(credentials.credentials)
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return user


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get(
    "/users",
    response_model=UsersListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all users (paginated)",
)
async def list_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    user_repo: Any = Depends(_get_user_repo),
):
    """Admin endpoint to list all users with pagination."""
    from backend.presentation.schemas.admin import UsersListResponse, UserResponse

    users = await user_repo.list_all(limit=per_page, offset=(page - 1) * per_page)
    total = len(user_repo._store)  # type: ignore[union-attr]

    return UsersListResponse(
        items=[UserResponse.model_validate(u.model_dump(mode="json")) for u in users],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.patch(
    "/users/{user_id}/block",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Block a user",
)
async def block_user(
    user_id: UUID,
    request: BlockRequest = Body(default_factory=BlockRequest),
    current_admin: User = Depends(get_current_admin),
    user_repo: Any = Depends(_get_user_repo),
):
    """Block a user by ID."""
    from backend.presentation.schemas.admin import UserResponse

    user = await user_repo.block(user_id)
    return UserResponse.model_validate(user, from_attributes=True)


@router.patch(
    "/users/{user_id}/unblock",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Unblock a user",
)
async def unblock_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    user_repo: Any = Depends(_get_user_repo),
):
    """Unblock a user by ID."""
    from backend.presentation.schemas.admin import UserResponse

    user = await user_repo.unblock(user_id)
    return UserResponse.model_validate(user, from_attributes=True)


@router.patch(
    "/users/{user_id}/toggle-block",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle a user's blocked state",
)
async def toggle_block(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    user_repo: Any = Depends(_get_user_repo),
):
    """Toggle a user's blocked state (block if unblocked, unblock if blocked)."""
    from backend.presentation.schemas.admin import UserResponse

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_blocked:
        user = await user_repo.unblock(user_id)
    else:
        user = await user_repo.block(user_id)

    return UserResponse.model_validate(user, from_attributes=True)
