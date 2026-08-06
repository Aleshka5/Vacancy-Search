"""Pydantic schemas for LLM config endpoints."""

from uuid import UUID

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field


class LLMConfigCreate(BaseModel):
    """Request body for POST /llm-configs."""

    provider: str
    model_name: str = "gpt-4"
    host: str | None = None
    api_key: str | None = None  # Only required for custom provider
    is_default: bool = False


class LLMConfigUpdate(BaseModel):
    """Request body for PUT /llm-configs/{id}."""

    model_name: str | None = None
    host: str | None = None
    api_key: str | None = None  # Only required for custom provider
    is_default: bool | None = None  # If True, set as default


class LLMConfigResponse(BaseModel):
    """Response body for LLM config endpoints."""

    id: UUID
    user_id: UUID
    provider: str
    model_name: str
    host: str | None
    api_key: str  # Decrypted plaintext
    is_default: bool
    created_at: str
    updated_at: str
