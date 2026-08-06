"""Domain interface — ILlmConfigRepository (pure, no SQLAlchemy)."""

from abc import ABC, abstractmethod
from uuid import UUID

from backend.domain.entities.llm_config import LLMConfig


class ILlmConfigRepository(ABC):
    """Repository interface for LLMConfig persistence."""

    @abstractmethod
    async def get_by_id(self, config_id: UUID) -> LLMConfig | None:
        """Find LLM config by UUID."""

    @abstractmethod
    async def get_by_id_and_user_id(
        self, config_id: UUID, user_id: UUID
    ) -> LLMConfig | None:
        """Find LLM config by ID, scoped to a user (IDOR protection)."""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> list[LLMConfig]:
        """Get all LLM configs for a user."""

    @abstractmethod
    async def get_default_by_user_id(self, user_id: UUID) -> LLMConfig | None:
        """Get the default LLM config for a user."""

    @abstractmethod
    async def create(self, config: LLMConfig) -> LLMConfig:
        """Create a new LLM config."""

    @abstractmethod
    async def update(self, config: LLMConfig) -> LLMConfig:
        """Update an existing LLM config (returns updated entity)."""

    @abstractmethod
    async def delete(self, config_id: UUID) -> LLMConfig:
        """Delete an LLM config."""

    @abstractmethod
    async def update_default(
        self, config_id: UUID, user_id: UUID
    ) -> LLMConfig | None:
        """Set a config as the user's default (clears others)."""
