"""Pydantic schemas for admin endpoints."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BlockRequest(BaseModel):
    """Request body for block/unblock operations."""

    reason: str | None = Field(
        default=None,
        description="Optional reason for blocking the user.",
    )


class UserResponse(BaseModel):
    """Response body for user operations."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    google_id: str
    email: str
    role: str
    is_blocked: bool
    default_llm_config_id: str | None = None
    created_at: str
    updated_at: str

    @field_validator("id", "google_id", "role", "default_llm_config_id", "created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_str(cls, v):
        return str(v) if v is not None else None


class UsersListResponse(BaseModel):
    """Paginated list of users."""

    items: list["UserResponse"]
    total: int
    page: int
    per_page: int
