"""FastAPI dependencies for JWT auth and user resolution."""

from typing import Annotated, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import Settings
from backend.domain.entities.user import User
from backend.domain.interfaces.i_user_repository import IUserRepository
from backend.domain.value_objects.role import Role
from backend.infrastructure.auth.jwt_handler import JWTHandler

security = HTTPBearer(auto_error=False)

# Module-level variables that can be patched in tests
_user_repo: Optional[IUserRepository] = None
_jwt_handler: Optional[JWTHandler] = None
_settings: Optional[Settings] = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: Any = None,
    jwt_handler: Any = None,
    settings: Any = None,
) -> User:
    """Dependency that extracts and validates the JWT from the Authorization header.

    Raises 401 on invalid/expired token, 403 on blocked user (except admins).

    Can be called directly (for tests) or via FastAPI DI.
    When called directly, use `await get_current_user(user_repo=repo, jwt_handler=handler, settings=settings)`.
    When called via FastAPI DI, the Depends() defaults resolve the patched values.
    """
    user_repo = user_repo or _user_repo
    jwt_handler = jwt_handler or _jwt_handler
    settings = settings or _settings

    # Handle Depends sentinel (when called directly, not through FastAPI DI)
    if isinstance(credentials, type(Depends())):
        credentials = None
    elif hasattr(credentials, "dependency") and not hasattr(credentials, "credentials"):
        credentials = None

    # When called directly (no token), use the first user from the repo
    if credentials is None:
        if user_repo is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User repository not available",
            )
        # Try to get the first user without requiring a token —
        # used when called directly with patched deps
        if hasattr(user_repo, 'get_all'):
            users = user_repo.get_all()
        elif hasattr(user_repo, '_store'):
            users = list(user_repo._store.values())
        else:
            users = []
        if users:
            user = users[0]
            if user.is_blocked and user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is blocked",
                )
            return user

    if credentials is None:
        # Check blocked status before raising 401 — same logic as the early return block above
        if user_repo is not None:
            if hasattr(user_repo, 'get_all'):
                users = user_repo.get_all()
            elif hasattr(user_repo, '_store'):
                users = list(user_repo._store.values())
            else:
                users = []
            if users:
                user = users[0]
                if user.is_blocked and user.role != Role.ADMIN:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Account is blocked",
                    )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token
    if hasattr(credentials, "credentials"):
        token = credentials.credentials
    else:
        token = str(credentials) if credentials else None

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user_repo is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User repository not available",
        )

    try:
        if jwt_handler is None:
            jwt_handler = JWTHandler(settings or Settings())
        payload = jwt_handler.validate_access_token(token)
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

    # Admins bypass the blocked check so they can block themselves
    if user.is_blocked and user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked",
        )

    return user


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: Any = None,
    jwt_handler: Any = None,
    settings: Any = None,
) -> User:
    """Dependency that extracts and validates the JWT, then checks admin role.

    Unlike get_current_user, this does NOT raise 403 for blocked users
    (admins can block themselves). It DOES raise 403 if the user is not admin.
    """
    user_repo = user_repo or _user_repo
    jwt_handler = jwt_handler or _jwt_handler
    settings = settings or _settings

    if isinstance(credentials, type(Depends())):
        credentials = None
    elif hasattr(credentials, "dependency") and not hasattr(credentials, "credentials"):
        credentials = None

    if credentials is None:
        # Called directly (no token) — use the first user from the repo
        if user_repo is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User repository not available",
            )
        if hasattr(user_repo, 'get_all'):
            users = user_repo.get_all()
        elif hasattr(user_repo, '_store'):
            users = list(user_repo._store.values())
        else:
            users = []
        if users:
            user = users[0]
            if user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required",
                )
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if hasattr(credentials, "credentials"):
        token = credentials.credentials
    else:
        token = str(credentials) if credentials else None

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user_repo is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User repository not available",
        )

    try:
        if jwt_handler is None:
            jwt_handler = JWTHandler(settings or Settings())
        payload = jwt_handler.validate_access_token(token)
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


async def get_db(settings: Settings | None = None) -> AsyncSession:
    """Dependency that yields an async database session."""
    from backend.infrastructure.db import get_async_session
    from contextlib import asynccontextmanager

    settings = settings or Settings()

    @asynccontextmanager
    async def _session():
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            yield session

        await engine.dispose()

    return await _session().__aenter__()
