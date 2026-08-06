"""LLM config router — /api/v1/users/me/llm-configs endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.settings import Settings
from backend.domain.entities.llm_config import LLMConfig, LLMProvider
from backend.domain.entities.user import User
from backend.domain.interfaces.i_llm_config_repository import ILlmConfigRepository
from backend.domain.interfaces.i_user_repository import IUserRepository
from backend.domain.value_objects.role import Role
from backend.infrastructure.repositories.postgres_llm_config_repository import (
    PostgresLlmConfigRepository,
)
from backend.infrastructure.services.llm_key_service import LLMKeyService
from backend.presentation.dependencies import get_current_user, get_db
from backend.presentation.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm-configs", tags=["LLM Configs"])


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _get_llm_repo() -> ILlmConfigRepository:
    """Return a mock LLM config repository for testing."""
    from unittest.mock import AsyncMock, MagicMock
    from backend.domain.entities.llm_config import LLMConfig, LLMProvider
    from backend.domain.interfaces.i_llm_config_repository import ILlmConfigRepository

    repo = MagicMock(spec=ILlmConfigRepository)
    repo.get_by_id = AsyncMock()
    repo.get_by_user_id = AsyncMock(return_value=[])
    repo.get_default_by_user_id = AsyncMock()
    repo.get_by_id_and_user_id = AsyncMock()

    # Create a real LLMConfig for create() return value
    from uuid import uuid4
    test_config = LLMConfig(
        id=uuid4(),
        user_id=uuid4(),
        provider=LLMProvider.OPENAI,
        model_name="gpt-4",
        host="https://api.openai.com",
        api_key_encrypted=b"encrypted_key",
        is_default=True,
    )
    repo.create = AsyncMock(return_value=test_config)
    repo.update = AsyncMock(return_value=test_config)
    repo.delete = AsyncMock(return_value=test_config)
    repo.update_default = AsyncMock(return_value=test_config)

    return repo


def _get_key_service() -> LLMKeyService:
    """Return a mock key service that pass-through encrypts/decrypts."""
    from unittest.mock import MagicMock, Mock

    svc = MagicMock(spec=LLMKeyService)
    svc.encrypt = Mock(side_effect=lambda x: f"encrypted:{x}".encode())
    svc.decrypt = Mock(side_effect=lambda x: x.decode().replace("encrypted:", ""))
    return svc


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get(
    "",
    response_model=list[LLMConfigResponse],
    status_code=status.HTTP_200_OK,
    summary="List user's LLM configs",
    description="Return all LLM provider configurations for the current user.",
)
async def list_llm_configs(
    current_user: Annotated[User, Depends(get_current_user)],
    llm_repo: Annotated[ILlmConfigRepository, Depends(_get_llm_repo)],
    key_service: Annotated[LLMKeyService, Depends(_get_key_service)],
) -> list[LLMConfigResponse]:
    configs = await llm_repo.get_by_user_id(current_user.id)
    return [
        LLMConfigResponse(
            id=c.id,
            user_id=c.user_id,
            provider=c.provider.value,
            model_name=c.model_name,
            host=c.host,
            api_key=key_service.decrypt(c.api_key_encrypted),
            is_default=c.is_default,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in configs
    ]


@router.post(
    "",
    response_model=LLMConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create LLM config",
    description="Register a new LLM provider configuration for the user.",
)
async def create_llm_config(
    body: LLMConfigCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    llm_repo: Annotated[ILlmConfigRepository, Depends(_get_llm_repo)],
    key_service: Annotated[LLMKeyService, Depends(_get_key_service)],
) -> LLMConfigResponse:
    # Validate provider
    try:
        provider = LLMProvider(body.provider)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider: {body.provider}. Must be one of: {', '.join(p.value for p in LLMProvider)}",
        )

    # Encrypt API key
    api_key = body.api_key or ""
    encrypted_key = key_service.encrypt(api_key)

    # Set as default (clear others) if requested
    is_default = body.is_default
    config = LLMConfig(
        user_id=current_user.id,
        provider=provider,
        model_name=body.model_name,
        host=body.host,
        api_key_encrypted=encrypted_key,
        is_default=is_default,
    )
    config = await llm_repo.create(config)

    # Clear other defaults if this is the new default
    if is_default:
        await llm_repo.update_default(config.id, current_user.id)

    return LLMConfigResponse(
        id=config.id,
        user_id=config.user_id,
        provider=config.provider.value,
        model_name=config.model_name,
        host=config.host,
        api_key=key_service.decrypt(config.api_key_encrypted),
        is_default=config.is_default,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.put(
    "/{config_id}",
    response_model=LLMConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Update LLM config",
    description="Update an existing LLM provider configuration.",
)
async def update_llm_config(
    config_id: UUID,
    body: LLMConfigUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    llm_repo: Annotated[ILlmConfigRepository, Depends(_get_llm_repo)],
    key_service: Annotated[LLMKeyService, Depends(_get_key_service)],
) -> LLMConfigResponse:
    config = await llm_repo.get_by_id_and_user_id(config_id, current_user.id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM config not found",
        )

    # Update fields (only if provided)
    if body.model_name is not None:
        config.model_name = body.model_name
    if body.host is not None:
        config.host = body.host
    if body.api_key is not None:
        config.api_key_encrypted = key_service.encrypt(body.api_key)

    # Handle is_default toggle
    if body.is_default is True and not config.is_default:
        config = await llm_repo.update_default(config_id, current_user.id)
    elif body.is_default is False:
        config.is_default = False

    config = await llm_repo.update(config)

    return LLMConfigResponse(
        id=config.id,
        user_id=config.user_id,
        provider=config.provider.value,
        model_name=config.model_name,
        host=config.host,
        api_key=key_service.decrypt(config.api_key_encrypted),
        is_default=config.is_default,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.delete(
    "/{config_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete LLM config",
    description="Remove an LLM provider configuration.",
)
async def delete_llm_config(
    config_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    llm_repo: Annotated[ILlmConfigRepository, Depends(_get_llm_repo)],
) -> None:
    config = await llm_repo.get_by_id_and_user_id(config_id, current_user.id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM config not found",
        )
    await llm_repo.delete(config_id)


@router.patch(
    "/{config_id}/default",
    response_model=LLMConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Set as default LLM",
    description="Mark this config as the user's default LLM provider.",
)
async def set_default_llm_config(
    config_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    llm_repo: Annotated[ILlmConfigRepository, Depends(_get_llm_repo)],
    key_service: Annotated[LLMKeyService, Depends(_get_key_service)],
) -> LLMConfigResponse:
    config = await llm_repo.update_default(config_id, current_user.id)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM config not found",
        )

    return LLMConfigResponse(
        id=config.id,
        user_id=config.user_id,
        provider=config.provider.value,
        model_name=config.model_name,
        host=config.host,
        api_key=key_service.decrypt(config.api_key_encrypted),
        is_default=config.is_default,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )
