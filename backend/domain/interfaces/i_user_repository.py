"""Domain interface — IUserRepository (pure, no SQLAlchemy)."""

from abc import ABC, abstractmethod
from uuid import UUID

from backend.domain.entities.user import User


class IUserRepository(ABC):
    """Repository interface for User persistence."""

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
