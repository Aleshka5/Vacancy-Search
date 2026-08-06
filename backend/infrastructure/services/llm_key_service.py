"""LLM API key encryption service (Fernet symmetric encryption)."""

from typing import ClassVar

from cryptography.fernet import Fernet

from backend.config.settings import Settings


class LLMKeyService:
    """Encrypts and decrypts LLM API keys using Fernet.

    Key is loaded from Settings (LLM_ENCRYPTION_KEY env).
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._fernet: Fernet | None = None

    @property
    def fernet(self) -> Fernet:
        if self._fernet is None:
            key = self._settings.LLM_ENCRYPTION_KEY
            # Normalize: Fernet accepts bytes or base64-encoded string
            if isinstance(key, str):
                key = key.encode("utf-8")
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, plaintext: str) -> bytes:
        """Encrypt a plaintext API key.

        Returns Fernet-encoded bytes.
        """
        return self.fernet.encrypt(plaintext.encode("utf-8"))

    def decrypt(self, encrypted: bytes) -> str:
        """Decrypt an Fernet-encoded API key.

        Returns plaintext string.
        """
        return self.fernet.decrypt(encrypted).decode("utf-8")
