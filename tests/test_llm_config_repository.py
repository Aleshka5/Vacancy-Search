"""Unit tests for PostgresLlmConfigRepository."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.llm_config import LLMConfig, LLMProvider
from backend.infrastructure.models.llm_config import LlmConfig
from backend.infrastructure.repositories.postgres_llm_config_repository import (
    PostgresLlmConfigRepository,
)


@pytest.fixture
def mock_session() -> AsyncSession:
    session = MagicMock(spec=AsyncSession)
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def repo(mock_session: AsyncSession) -> PostgresLlmConfigRepository:
    return PostgresLlmConfigRepository(mock_session)


@pytest.fixture
def sample_domain_config() -> LLMConfig:
    return LLMConfig(
        user_id=uuid4(),
        provider=LLMProvider.OPENAI,
        model_name="gpt-4",
        host="https://api.openai.com",
        api_key_encrypted=b"encrypted_key",
        is_default=True,
    )


def _make_row(id: UUID | None = None, **kwargs) -> LlmConfig:
    """Create a fake LlmConfig row."""
    return LlmConfig(
        id=id or uuid4(),
        user_id=uuid4(),
        provider=kwargs.get("provider", "openai"),
        model_name=kwargs.get("model_name", "gpt-4"),
        host=kwargs.get("host"),
        api_key_encrypted=b"key",
        is_default=kwargs.get("is_default", False),
    )


async def test_create_config(repo: PostgresLlmConfigRepository) -> None:
    """Test creating a config."""
    config = LLMConfig(
        user_id=uuid4(),
        provider=LLMProvider.OPENAI,
        api_key_encrypted=b"test_key",
    )
    result = await repo.create(config)
    repo._db.add.assert_called_once()
    repo._db.commit.assert_called_once()
    assert result is config


async def test_update_default_clears_others(
    repo: PostgresLlmConfigRepository,
) -> None:
    """Test that update_default clears is_default on other configs."""
    target_id = uuid4()
    target_user = uuid4()

    # Create rows with proper datetime values
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    target_row = LlmConfig(
        id=target_id,
        user_id=target_user,
        provider="openai",
        model_name="gpt-4",
        api_key_encrypted=b"key",
        is_default=False,
        created_at=now,
        updated_at=now,
    )
    other_row = LlmConfig(
        id=uuid4(),
        user_id=target_user,
        provider="anthropic",
        model_name="claude-3",
        api_key_encrypted=b"key",
        is_default=True,
        created_at=now,
        updated_at=now,
    )

    call_count = [0]

    def mock_execute(stmt):
        from sqlalchemy import inspect as sa_inspect

        call_count[0] += 1
        if call_count[0] == 1:
            # First call: select other defaults
            scalar_mock = MagicMock()
            scalar_mock.all.return_value = [other_row]
            result_mock = MagicMock()
            result_mock.scalars.return_value = scalar_mock
            return result_mock
        # Second call: select target
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = target_row
        return result_mock

    repo._db.execute.side_effect = mock_execute
    repo._db.commit = AsyncMock()
    repo._db.refresh = AsyncMock()

    result = await repo.update_default(target_id, target_user)

    assert result is not None
    assert result.is_default is True
    assert other_row.is_default is False


async def test_delete_config(repo: PostgresLlmConfigRepository) -> None:
    """Test deleting a config."""
    config_id = uuid4()
    row = _make_row(id=config_id)

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = row
    repo._db.execute.return_value = result_mock

    result = await repo.delete(config_id)

    repo._db.delete.assert_called_once_with(row)
    repo._db.commit.assert_called_once()
