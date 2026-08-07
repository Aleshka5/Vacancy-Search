"""Fake IUserRepository for unit tests and development."""

import asyncio
from uuid import UUID, uuid4

from backend.domain.entities.user import User
from backend.domain.interfaces.i_user_repository import IUserRepository


class FakeUserRepository(IUserRepository):
    """In-memory user repository for testing."""

    def __init__(self) -> None:
        self._store: dict[str, User] = {}
        self._by_google_id: dict[str, UUID] = {}
        self._by_email: dict[str, UUID] = {}

    async def get_by_google_id(self, google_id: str) -> User | None:
        user_id = self._by_google_id.get(google_id)
        return self._store.get(str(user_id)) if user_id else None

    async def get_by_email(self, email: str) -> User | None:
        user_id = self._by_email.get(email)
        return self._store.get(str(user_id)) if user_id else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._store.get(str(user_id))

    def get_by_id_sync(self, user_id: str | UUID) -> User | None:
        """Synchronous version of get_by_id — used by dependencies.py."""
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
        try:
            return asyncio.get_running_loop().run_until_complete(
                self.get_by_id(uid)
            )
        except RuntimeError:
            return asyncio.run(self.get_by_id(uid))

    async def create(self, user: User) -> User:
        key = str(user.id)
        self._store[key] = user
        self._by_google_id[user.google_id] = user.id
        self._by_email[user.email] = user.id
        return user

    async def update(self, user: User) -> User:
        key = str(user.id)
        self._store[key] = user
        return user

    async def block(self, user_id: UUID) -> User:
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        user.is_blocked = True
        await self.update(user)
        return user

    async def unblock(self, user_id: UUID) -> User:
        user = await self.get_by_id(user_id)
        if user is None:
            raise ValueError(f"User not found: {user_id}")
        user.is_blocked = False
        await self.update(user)
        return user

    async def _list_page(self, page: int, limit: int) -> list[User]:
        return list(self._store.values())[page * limit : (page + 1) * limit]
