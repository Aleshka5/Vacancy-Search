"""PostgreSQL implementation of IUserRepository (async SQLAlchemy)."""

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import String
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.user import User
from backend.domain.interfaces.i_user_repository import IUserRepository
from backend.domain.value_objects.role import Role

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class UserTable(Base):
    """SQLAlchemy-mapped User table."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    google_id: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="USER")
    is_blocked: Mapped[bool] = mapped_column(default=False)
    default_llm_config_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[str] = mapped_column(String(36))
    updated_at: Mapped[str] = mapped_column(String(36))


class PostgresUserRepository(IUserRepository):
    """Async SQLAlchemy repository for User."""

    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def get_by_google_id(self, google_id: str) -> User | None:
        """Find user by Google OAuth ID."""
        stmt = select(UserTable).where(UserTable.google_id == google_id)
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return self._row_to_user(row)

    async def get_by_email(self, email: str) -> User | None:
        """Find user by email."""
        stmt = select(UserTable).where(UserTable.email == email)
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return self._row_to_user(row)

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Find user by UUID."""
        stmt = select(UserTable).where(UserTable.id == str(user_id))
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return self._row_to_user(row)

    def get_by_id_sync(self, user_id: UUID) -> User | None:
        """Synchronous version of get_by_id — used by dependencies.py."""
        try:
            return asyncio.get_running_loop().run_until_complete(
                self.get_by_id(user_id)
            )
        except RuntimeError:
            return asyncio.run(self.get_by_id(user_id))

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
        stmt = select(UserTable).where(UserTable.id == str(user_id))
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"User not found: {user_id}")
        row.is_blocked = True
        await self.update(row)
        return row

    async def unblock(self, user_id: UUID) -> User:
        """Unblock a user."""
        stmt = select(UserTable).where(UserTable.id == str(user_id))
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"User not found: {user_id}")
        row.is_blocked = False
        await self.update(row)
        return row

    async def _list_page(self, page: int, limit: int) -> list[User]:
        """Fetch one page of users from the DB."""
        stmt = select(UserTable).offset(page * limit).limit(limit).order_by(UserTable.id)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """Fetch all users in a single SQL query."""
        stmt = select(UserTable).order_by(UserTable.id).offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    def _row_to_user(self, row: UserTable) -> User:
        """Convert a SQLAlchemy row to the domain User entity."""
        from datetime import datetime, timezone

        try:
            created = datetime.fromisoformat(row.created_at.replace("+00:00", "+0000")).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            created = datetime.now(timezone.utc)
        try:
            updated = datetime.fromisoformat(row.updated_at.replace("+00:00", "+0000")).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            updated = datetime.now(timezone.utc)

        return User(
            id=UUID(row.id),
            google_id=row.google_id,
            email=row.email,
            role=Role(row.role),
            is_blocked=row.is_blocked,
            default_llm_config_id=UUID(row.default_llm_config_id) if row.default_llm_config_id else None,
            created_at=created,
            updated_at=updated,
        )
