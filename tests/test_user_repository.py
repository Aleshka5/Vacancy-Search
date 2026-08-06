"""Unit tests for FakeUserRepository."""

from uuid import uuid4

import pytest

from backend.domain.entities.user import User
from backend.domain.value_objects.role import Role
from backend.infrastructure.repositories.fake_user_repository import FakeUserRepository


@pytest.fixture
def repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def sample_user() -> User:
    return User(
        id=uuid4(),
        google_id="google-123",
        email="test@example.com",
        role=Role.USER,
    )


async def test_create_user(repo: FakeUserRepository, sample_user: User) -> None:
    created = await repo.create(sample_user)
    assert created.id == sample_user.id
    assert created.google_id == "google-123"
    assert created.email == "test@example.com"


async def test_get_by_google_id(repo: FakeUserRepository, sample_user: User) -> None:
    await repo.create(sample_user)
    found = await repo.get_by_google_id("google-123")
    assert found is not None
    assert found.email == "test@example.com"


async def test_get_by_google_id_not_found(repo: FakeUserRepository) -> None:
    found = await repo.get_by_google_id("nonexistent")
    assert found is None


async def test_get_by_email(repo: FakeUserRepository, sample_user: User) -> None:
    await repo.create(sample_user)
    found = await repo.get_by_email("test@example.com")
    assert found is not None
    assert found.google_id == "google-123"


async def test_update_user(repo: FakeUserRepository, sample_user: User) -> None:
    await repo.create(sample_user)
    sample_user.email = "new@example.com"
    sample_user.role = Role.ADMIN
    updated = await repo.update(sample_user)
    assert updated.email == "new@example.com"
    assert updated.role == Role.ADMIN


async def test_block_user(repo: FakeUserRepository, sample_user: User) -> None:
    await repo.create(sample_user)
    blocked = await repo.block(sample_user.id)
    assert blocked.is_blocked is True


async def test_unblock_user(repo: FakeUserRepository, sample_user: User) -> None:
    await repo.create(sample_user)
    blocked = await repo.block(sample_user.id)
    assert blocked.is_blocked is True
    unblocked = await repo.unblock(sample_user.id)
    assert unblocked.is_blocked is False


async def test_block_nonexistent_user(repo: FakeUserRepository) -> None:
    with pytest.raises(ValueError):
        await repo.block(uuid4())
