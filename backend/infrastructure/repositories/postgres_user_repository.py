"""PostgreSQL implementation of IUserRepository (async SQLAlchemy)."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.user import User
from backend.domain.interfaces.i_user_repository import IUserRepository
from backend.domain.value_objects.role import Role

logger = logging.getLogger(__name__)


class PostgresUserRepository(IUserRepository):
    """Async SQLAlchemy repository for User."""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def get_by_google_id(self, google_id: str) -> User | None:
        """Find user by Google OAuth ID."""
        stmt = select(User).where(User.google_id == google_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Find user by email."""
        stmt = select(User).where(User.email == email)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Find user by UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Create a new user."""
        await self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        logger.info("Created user: %s (%s)", user.email, user.google_id)
        return user

    async def update(self, user: User) -> User:
        """Update an existing user."""
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def block(self, user_id: UUID) -> User:
        """Block a user."""
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        user.is_blocked = True
        await self.update(user)
        return user

    async def unblock(self, user_id: UUID) -> User:
        """Unblock a user."""
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        user.is_blocked = False
        await self.update(user)
        return user
