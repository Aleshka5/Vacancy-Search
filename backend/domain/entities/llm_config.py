"""Domain entity — LLMConfig (pure, no SQLAlchemy/FastAPI)."""

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field, PrivateAttr


class LLMProvider(str, Enum):
    """LLM provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    CUSTOM = "custom"


class LLMConfig(BaseModel):
    """User's LLM provider configuration.

    All IDs are UUID, timestamps are UTC datetime.
    API keys are stored encrypted (bytes) in the database.
    """

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    provider: LLMProvider
    model_name: str = "gpt-4"
    host: str | None = None
    api_key_encrypted: bytes
    is_default: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Private attribute for Fernet key (not serialized)
    _key: bytes = PrivateAttr(default_factory=Fernet.generate_key)

    @property
    def api_key(self) -> str | None:
        """Decrypt and return the plaintext API key."""
        fernet = Fernet(self._key)
        return fernet.decrypt(self.api_key_encrypted).decode("utf-8")

    def encrypt_api_key(self, plaintext: str) -> None:
        """Encrypt a plaintext API key into api_key_encrypted."""
        self._key = Fernet.generate_key()
        fernet = Fernet(self._key)
        self.api_key_encrypted = fernet.encrypt(plaintext.encode("utf-8"))

    def rekey(self, plaintext: str) -> None:
        """Re-encrypt with a new key (useful for rotation)."""
        self._key = Fernet.generate_key()
        fernet = Fernet(self._key)
        self.api_key_encrypted = fernet.encrypt(plaintext.encode("utf-8"))

    def set_key(self, encrypted: bytes, fernet_key: bytes) -> None:
        """Set the encrypted key and store the Fernet key for decryption."""
        self.api_key_encrypted = encrypted
        self._key = fernet_key
