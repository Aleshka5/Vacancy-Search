"""Unit tests for LLMConfig entity."""

from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet

from backend.domain.entities.llm_config import LLMConfig, LLMProvider


@pytest.fixture
def sample_config() -> LLMConfig:
    return LLMConfig(
        user_id=uuid4(),
        provider=LLMProvider.OPENAI,
        model_name="gpt-4",
        host="https://api.openai.com",
        api_key_encrypted=b"encrypted_key_bytes",
        is_default=True,
    )


def test_llm_config_defaults() -> None:
    """Test LLMConfig model defaults."""
    config = LLMConfig(
        user_id=uuid4(),
        provider=LLMProvider.OPENAI,
        api_key_encrypted=b"test",
    )
    assert config.model_name == "gpt-4"
    assert config.host is None
    assert config.is_default is False
    assert isinstance(config.created_at, object)  # datetime-like
    assert isinstance(config.updated_at, object)


def test_llm_config_with_all_fields() -> None:
    """Test LLMConfig with all fields specified."""
    config_id = uuid4()
    user_id = uuid4()
    config = LLMConfig(
        id=config_id,
        user_id=user_id,
        provider=LLMProvider.ANTHROPIC,
        model_name="claude-3-opus",
        host="https://api.anthropic.com",
        api_key_encrypted=b"encrypted_key",
        is_default=True,
    )
    assert config.id == config_id
    assert config.user_id == user_id
    assert config.provider == LLMProvider.ANTHROPIC
    assert config.model_name == "claude-3-opus"
    assert config.host == "https://api.anthropic.com"
    assert config.is_default is True


def test_llm_provider_enum() -> None:
    """Test LLMProvider enum values."""
    assert LLMProvider.OPENAI == "openai"
    assert LLMProvider.ANTHROPIC == "anthropic"
    assert LLMProvider.OLLAMA == "ollama"
    assert LLMProvider.CUSTOM == "custom"


def test_encrypt_and_decrypt_api_key() -> None:
    """Test that encrypt/decrypt round-trips correctly."""
    plaintext = "sk-test-key-12345"
    config = LLMConfig(
        user_id=uuid4(),
        provider=LLMProvider.CUSTOM,
        api_key_encrypted=b"placeholder",
    )
    config.encrypt_api_key(plaintext)

    # Check encrypted is bytes
    assert isinstance(config.api_key_encrypted, bytes)

    # Decrypt and verify
    decrypted = config.api_key
    assert decrypted == plaintext


def test_rekey_api_key() -> None:
    """Test rekeying (rotation) of the API key."""
    plaintext = "sk-new-key"
    config = LLMConfig(
        user_id=uuid4(),
        provider=LLMProvider.OPENAI,
        api_key_encrypted=b"old",
    )
    config.encrypt_api_key("sk-old-key")
    old_encrypted = config.api_key_encrypted

    config.rekey(plaintext)

    assert config.api_key_encrypted != old_encrypted
    assert config.api_key == plaintext


def test_set_key_directly() -> None:
    """Test setting encrypted key directly."""
    fernet_key = Fernet.generate_key()
    fernet = Fernet(fernet_key)
    encrypted = fernet.encrypt(b"direct-key")

    config = LLMConfig(
        user_id=uuid4(),
        provider=LLMProvider.OPENAI,
        api_key_encrypted=b"placeholder",
    )
    config.set_key(encrypted, fernet_key)

    assert config.api_key == "direct-key"
