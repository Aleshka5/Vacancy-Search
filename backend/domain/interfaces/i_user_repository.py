"""Domain interface — IUserRepository (pure, no SQLAlchemy)."""

from abc import ABC, abstractmethod
from uuid import UUID

from backend.domain.entities.user import User


class IUserRepository(ABC):
    """Repository interface for User persistence."""

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """Return all users (default 100).  Sub-classes may override for SQL optimisation."""
        users: list[User] = []
        page = 0
        while len(users) < limit:
            chunk = await self._list_page(page, limit)
            if not chunk:
                break
            users.extend(chunk)
            page += 1
        return users[offset : offset + limit]

    @abstractmethod
    async def _list_page(self, page: int, limit: int) -> list[User]:
        """Fetch one page of users (page 0-based)."""

    @abstractmethod
    async def get_by_google_id(self, google_id: str) -> User | None:
        """Find user by Google OAuth ID."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Find user by email."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Find user by UUID."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user (returns updated entity)."""

    @abstractmethod
    async def block(self, user_id: UUID) -> User:
        """Block a user."""

    @abstractmethod
    async def unblock(self, user_id: UUID) -> User:
        """Unblock a user."""
