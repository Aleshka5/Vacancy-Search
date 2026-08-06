"""SQLAlchemy model for LLMConfig.

The domain entity (LLMConfig) is a pure Pydantic model.
This is the mapping class that SQLAlchemy uses to read/write
the llm_configs table.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from backend.infrastructure.db import Base


class LlmConfig(Base):
    """SQLAlchemy ORM model for llm_configs table."""

    __tablename__ = "llm_configs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, default="gpt-4")
    host: Mapped[str | None] = mapped_column(String, nullable=True)
    api_key_encrypted: Mapped[bytes] = mapped_column(Text, nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_llm_configs_user_default"),
    )
