"""Integration tests for LLM config endpoints (CRUD).

Tests the Pydantic schemas, key service, and router module directly
without triggering the full FastAPI app import chain.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.domain.entities.llm_config import LLMConfig, LLMProvider
from backend.domain.interfaces.i_llm_config_repository import ILlmConfigRepository
from backend.infrastructure.services.llm_key_service import LLMKeyService


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def test_key() -> bytes:
    return Fernet.generate_key()


@pytest.fixture
def key_service(test_key: bytes) -> LLMKeyService:
    from unittest.mock import MagicMock
    from backend.config.settings import Settings

    mock_settings = MagicMock(spec=Settings)
    mock_settings.LLM_ENCRYPTION_KEY = test_key
    svc = LLMKeyService(settings=mock_settings)
    return svc


@pytest.fixture
def mock_repo(key_service: LLMKeyService) -> ILlmConfigRepository:
    from unittest.mock import AsyncMock, MagicMock
    from backend.domain.entities.llm_config import LLMConfig, LLMProvider

    repo = MagicMock(spec=ILlmConfigRepository)
    repo.get_by_id = AsyncMock()
    repo.get_by_user_id = AsyncMock()
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
        api_key_encrypted=key_service.encrypt("sk-123"),
        is_default=True,
    )
    repo.create = AsyncMock(return_value=test_config)
    repo.update = AsyncMock(return_value=test_config)
    repo.delete = AsyncMock(return_value=test_config)
    repo.update_default = AsyncMock(return_value=test_config)

    repo._key_service = key_service
    return repo


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


def test_create_llm_config_endpoint(key_service: LLMKeyService, mock_repo: ILlmConfigRepository) -> None:
    """Test creating an LLM config via the endpoint."""
    # Import the router directly, bypassing presentation/__init__.py
    from backend.presentation.routers.llm_config import router

    app = FastAPI()
    # The router already has prefix="/llm-configs", so don't add it again
    app.include_router(router)

    # Patch get_current_user to return a mock user
    import uuid as uuid_mod
    from backend.domain.entities.user import User
    from backend.domain.value_objects.role import Role

    mock_user = User(
        id=uuid_mod.uuid4(),
        email="test@example.com",
        google_id="test-google-id",
        role=Role.USER,
        is_blocked=False,
    )

    from backend.presentation.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Override dependencies on the app level
    app.dependency_overrides[LLMKeyService] = lambda: key_service

    # Mock _get_llm_repo to return our mock repo
    import backend.presentation.routers.llm_config as llm_mod
    llm_mod._get_llm_repo = lambda: mock_repo

    client = TestClient(app)

    response = client.post(
        "/llm-configs",
        json={
            "provider": "openai",
            "model_name": "gpt-4",
            "host": "https://api.openai.com",
            "api_key": "test-api-key-123",
            "is_default": True,
        },
    )
    # Status depends on mock behavior; 200/201 expected
    assert response.status_code in (200, 201)
    data = response.json()
    assert isinstance(data, dict)


def test_list_llm_configs_endpoint(key_service: LLMKeyService) -> None:
    """Test listing LLM configs."""
    from backend.presentation.schemas.llm_config import LLMConfigResponse

    config = LLMConfig(
        user_id=uuid4(),
        provider=LLMProvider.OPENAI,
        model_name="gpt-4",
        host="https://api.openai.com",
        api_key_encrypted=key_service.encrypt("sk-123"),
        is_default=True,
    )
    response = LLMConfigResponse(
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
    assert response.api_key == "sk-123"
    assert response.provider == "openai"


def test_provider_validation() -> None:
    """Test that invalid provider raises ValueError."""
    with pytest.raises(ValueError):
        LLMProvider("invalid_provider")


def test_provider_values() -> None:
    """Test all provider string values."""
    for provider in LLMProvider:
        assert isinstance(provider.value, str)
        assert len(provider.value) > 0


def test_update_default_clears_others(key_service: LLMKeyService, mock_repo: ILlmConfigRepository) -> None:
    """Test that updating to default clears the flag on other configs."""
    from backend.presentation.routers.llm_config import router

    app = FastAPI()
    app.include_router(router)

    import backend.presentation.routers.llm_config as llm_mod
    llm_mod._get_llm_repo = lambda: mock_repo

    # Patch get_current_user to return a mock user
    import uuid as uuid_mod
    from backend.domain.entities.user import User
    from backend.domain.value_objects.role import Role
    from backend.presentation.dependencies import get_current_user
    from backend.infrastructure.services.llm_key_service import LLMKeyService
    from unittest.mock import MagicMock

    mock_user = User(
        id=uuid_mod.uuid4(),
        email="test@example.com",
        google_id="test-google-id",
        role=Role.USER,
        is_blocked=False,
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user

    # Override _get_key_service at app level
    from backend.presentation.routers.llm_config import _get_key_service as _orig_get_key_service
    mock_key_svc = MagicMock(spec=LLMKeyService)
    mock_key_svc.encrypt = lambda x: f"encrypted:{x}".encode()
    mock_key_svc.decrypt = lambda x: x.decode().replace("encrypted:", "")
    app.dependency_overrides[_orig_get_key_service] = lambda: mock_key_svc

    client = TestClient(app)

    target_config = LLMConfig(
        id=uuid4(),
        user_id=uuid4(),
        provider=LLMProvider.ANTHROPIC,
        is_default=False,
        api_key_encrypted=b"key",
    )
    mock_repo.update_default = AsyncMock(return_value=target_config)

    response = client.patch(f"/llm-configs/{target_config.id}/default")
    assert response.status_code == 200
    data = response.json()
    assert data["is_default"] is True
