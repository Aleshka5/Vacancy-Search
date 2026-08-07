"""RS256 JWT handler — generates, validates, and decodes JWTs."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from jose import JWTError, jwt

from backend.config.settings import Settings


class JWTHandler:
    """Handles RS256 JWT operations."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._algorithm = settings.JWT_ALGORITHM
        self._access_exp = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        self._refresh_exp = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        self._iss = settings.APP_NAME

    # ------------------------------------------------------------------
    # Helpers to load keys
    # ------------------------------------------------------------------

    @property
    def _private_key(self) -> str:
        key = self._settings.JWT_PRIVATE_KEY
        if isinstance(key, Path):
            return key.read_text()
        key_str = str(key)
        if key_str.strip().startswith("-----"):
            return key_str
        if Path(key_str).is_file():
            return Path(key_str).read_text()
        return key_str

    @property
    def _public_key(self) -> str:
        key = self._settings.JWT_PUBLIC_KEY
        if isinstance(key, Path):
            return key.read_text()
        key_str = str(key)
        if key_str.strip().startswith("-----"):
            return key_str
        if Path(key_str).is_file():
            return Path(key_str).read_text()
        return key_str

    # ------------------------------------------------------------------
    # Token generation
    # ------------------------------------------------------------------

    def generate_access_token(self, user_id: UUID) -> str:
        """Create a short-lived access token (15 min)."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "exp": now + self._access_exp,
            "iat": now,
            "iss": self._iss,
            "type": "access",
        }
        return jwt.encode(payload, str(self._private_key), algorithm=self._algorithm)

    def generate_refresh_token(self, user_id: UUID) -> str:
        """Create a long-lived refresh token (30 days)."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "exp": now + self._refresh_exp,
            "iat": now,
            "iss": self._iss,
            "type": "refresh",
        }
        return jwt.encode(payload, str(self._private_key), algorithm=self._algorithm)

    # ------------------------------------------------------------------
    # Token validation
    # ------------------------------------------------------------------

    def decode_token(self, token: str) -> dict:
        """Validate and decode a JWT. Raises JWTError on failure."""
        return jwt.decode(
            token,
            str(self._public_key),
            algorithms=[self._algorithm],
            issuer=self._iss,
        )

    def validate_access_token(self, token: str) -> dict:
        """Decode access token and verify it's an access token."""
        payload = self.decode_token(token)
        if payload.get("type") != "access":
            raise JWTError("Invalid token type: expected access")
        return payload

    def validate_refresh_token(self, token: str) -> dict:
        """Decode refresh token and verify it's a refresh token."""
        payload = self.decode_token(token)
        if payload.get("type") != "refresh":
            raise JWTError("Invalid token type: expected refresh")
        return payload

    def validate_token(self, token: str) -> tuple[dict, str]:
        """Validate any JWT and return (payload, token_type).

        Raises JWTError on validation failure (expired, bad signature, etc.).
        """
        payload = self.decode_token(token)
        token_type = payload.get("type", "unknown")
        return payload, token_type
