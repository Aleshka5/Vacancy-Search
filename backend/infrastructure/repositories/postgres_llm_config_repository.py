"""PostgreSQL implementation of ILlmConfigRepository (async SQLAlchemy)."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.llm_config import LLMConfig, LLMProvider
from backend.domain.interfaces.i_llm_config_repository import ILlmConfigRepository
from backend.infrastructure.models.llm_config import LlmConfig

logger = logging.getLogger(__name__)


def _to_domain(row: LlmConfig) -> LLMConfig:
    """Convert SQLAlchemy row to domain entity."""
    return LLMConfig(
        id=row.id,
        user_id=row.user_id,
        provider=LLMProvider(row.provider),
        model_name=row.model_name,
        host=row.host,
        api_key_encrypted=row.api_key_encrypted,
        is_default=row.is_default,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class PostgresLlmConfigRepository(ILlmConfigRepository):
    """Async SQLAlchemy repository for LLMConfig."""

    def __init__(self, db_session: AsyncSession) -> None:
        self._db = db_session

    async def get_by_id(self, config_id: UUID) -> LLMConfig | None:
        stmt = select(LlmConfig).where(LlmConfig.id == config_id)
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def get_by_id_and_user_id(
        self, config_id: UUID, user_id: UUID
    ) -> LLMConfig | None:
        stmt = select(LlmConfig).where(
            LlmConfig.id == config_id,
            LlmConfig.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def get_by_user_id(self, user_id: UUID) -> list[LLMConfig]:
        stmt = select(LlmConfig).where(LlmConfig.user_id == user_id)
        result = await self._db.execute(stmt)
        rows = result.scalars().all()
        return [_to_domain(r) for r in rows]

    async def get_default_by_user_id(self, user_id: UUID) -> LLMConfig | None:
        stmt = select(LlmConfig).where(
            LlmConfig.user_id == user_id,
            LlmConfig.is_default,
        ).limit(1)
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def create(self, config: LLMConfig) -> LLMConfig:
        row = LlmConfig(
            id=config.id,
            user_id=config.user_id,
            provider=config.provider.value,
            model_name=config.model_name,
            host=config.host,
            api_key_encrypted=config.api_key_encrypted,
            is_default=config.is_default,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
        await self._db.add(row)
        await self._db.commit()
        await self._db.refresh(row)
        logger.info(
            "Created LLM config: %s (%s, user=%s)",
            row.id,
            row.provider,
            row.user_id,
        )
        return config

    async def update(self, config: LLMConfig) -> LLMConfig:
        stmt = select(LlmConfig).where(LlmConfig.id == config.id)
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None:
            row.model_name = config.model_name
            row.host = config.host
            row.api_key_encrypted = config.api_key_encrypted
            row.is_default = config.is_default
            row.updated_at = datetime.now(timezone.utc)
            await self._db.commit()
            await self._db.refresh(row)
        return config

    async def delete(self, config_id: UUID) -> LLMConfig:
        stmt = select(LlmConfig).where(LlmConfig.id == config_id)
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"LLMConfig not found: {config_id}")
        await self._db.delete(row)
        await self._db.commit()
        return row

    async def update_default(
        self, config_id: UUID, user_id: UUID
    ) -> LLMConfig | None:
        # Clear default on all other configs for this user
        stmt = select(LlmConfig).where(
            LlmConfig.user_id == user_id,
            LlmConfig.is_default,
            LlmConfig.id != config_id,
        )
        result = await self._db.execute(stmt)
        for row in result.scalars().all():
            row.is_default = False

        # Set the target as default
        stmt = select(LlmConfig).where(
            LlmConfig.id == config_id,
            LlmConfig.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None:
            row.is_default = True
            row.updated_at = datetime.now(timezone.utc)
            await self._db.commit()
            await self._db.refresh(row)
            return _to_domain(row)
        return None
