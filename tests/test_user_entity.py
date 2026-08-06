"""Unit tests for User entity."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.domain.entities.user import User
from backend.domain.value_objects.role import Role


def test_user_defaults() -> None:
    """Test User model defaults."""
    user = User(
        id=uuid4(),
        google_id="test-google-id",
        email="test@example.com",
    )
    assert user.role == Role.USER
    assert user.is_blocked is False
    assert user.default_llm_config_id is None
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_timestamps_are_utc() -> None:
    """Test that timestamps have UTC timezone."""
    user = User(
        id=uuid4(),
        google_id="test",
        email="test@example.com",
    )
    assert user.created_at.tzinfo is not None
    assert user.updated_at.tzinfo is not None


def test_user_role_enum() -> None:
    """Test Role enum values."""
    assert Role.USER == "USER"
    assert Role.ADMIN == "ADMIN"


def test_user_with_all_fields() -> None:
    """Test User with all fields specified."""
    user_id = uuid4()
    llm_id = uuid4()
    now = datetime.now(timezone.utc)
    user = User(
        id=user_id,
        google_id="g-123",
        email="admin@example.com",
        role=Role.ADMIN,
        is_blocked=True,
        default_llm_config_id=llm_id,
        created_at=now,
        updated_at=now,
    )
    assert user.id == user_id
    assert user.role == Role.ADMIN
    assert user.is_blocked is True
    assert user.default_llm_config_id == llm_id
