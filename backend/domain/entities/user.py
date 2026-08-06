"""Domain entity — User (pure, no SQLAlchemy/FastAPI/MinIO)."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from backend.domain.value_objects.role import Role


class User(BaseModel):
    """Authenticated user entity.

    All IDs are UUID, timestamps are UTC datetime.
    """

    id: UUID
    google_id: str
    email: str
    role: Role = Role.USER
    is_blocked: bool = False
    default_llm_config_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
