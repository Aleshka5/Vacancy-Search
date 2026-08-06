"""FastAPI dependencies for JWT auth and user resolution."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import Settings
from backend.domain.entities.user import User
from backend.domain.interfaces.i_user_repository import IUserRepository
from backend.infrastructure.auth.jwt_handler import JWTHandler

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user_repo: IUserRepository = Depends(),
    jwt_handler: JWTHandler = Depends(),
    settings: Settings = Depends(),
) -> User:
    """Dependency that extracts and validates the JWT from the Authorization header.

    Raises 401 on invalid/expired token, 403 on blocked user.
    """
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

    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked",
        )

    return user


async def get_db(settings: Settings = Depends()) -> AsyncSession:
    """Dependency that yields an async database session."""
    # Import here to avoid circular imports
    from backend.infrastructure.db import get_async_session

    # This is a placeholder — actual implementation connects to Postgres
    # via SQLAlchemy async engine. See infrastructure/db.py for details.
    from contextlib import asynccontextmanager

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
