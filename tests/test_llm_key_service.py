"""Unit tests for LLMKeyService (Fernet encryption)."""

from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from backend.domain.entities.llm_config import LLMConfig
from backend.infrastructure.services.llm_key_service import LLMKeyService


@pytest.fixture
def test_key() -> bytes:
    """32-byte base64-encoded Fernet key."""
    return Fernet.generate_key()


@pytest.fixture
def key_service(test_key: bytes) -> LLMKeyService:
    svc = LLMKeyService()
    svc._fernet = Fernet(test_key)
    return svc


def test_encrypt_and_decrypt(key_service: LLMKeyService) -> None:
    """Test Fernet encrypt/decrypt round-trip."""
    plaintext = "sk-ant-1234567890abcdef"
    encrypted = key_service.encrypt(plaintext)
    decrypted = key_service.decrypt(encrypted)
    assert decrypted == plaintext


def test_encrypt_returns_bytes(key_service: LLMKeyService) -> None:
    """Test that encrypt() returns bytes."""
    encrypted = key_service.encrypt("test")
    assert isinstance(encrypted, bytes)


def test_decrypt_returns_string(key_service: LLMKeyService) -> None:
    """Test that decrypt() returns a string."""
    encrypted = key_service.encrypt("test")
    result = key_service.decrypt(encrypted)
    assert isinstance(result, str)


def test_encrypt_decrypt_empty_string(key_service: LLMKeyService) -> None:
    """Test encryption of an empty API key (for Ollama)."""
    encrypted = key_service.encrypt("")
    decrypted = key_service.decrypt(encrypted)
    assert decrypted == ""
