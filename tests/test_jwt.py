"""Unit tests for JWTHandler."""

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
    load_pem_public_key,
)
from jose import JWTError

from backend.infrastructure.auth.jwt_handler import JWTHandler
from backend.config.settings import Settings


def _generate_keys() -> tuple[Path, Path]:
    """Generate temporary RSA key pair for testing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    )
    public_pem = private_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    tmp = Path(tempfile.mkdtemp())
    private_path = tmp / "private.pem"
    public_path = tmp / "public.pem"
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)
    return private_path, public_path


def _make_settings(private_key: Path, public_key: Path) -> Settings:
    return Settings(
        APP_NAME="TestApp",
        JWT_PRIVATE_KEY=private_key,
        JWT_PUBLIC_KEY=public_key,
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15,
        JWT_REFRESH_TOKEN_EXPIRE_DAYS=30,
    )


@pytest.fixture
def keys() -> tuple[Path, Path]:
    return _generate_keys()


@pytest.fixture
def settings(keys: tuple[Path, Path]) -> Settings:
    return _make_settings(*keys)


@pytest.fixture
def jwt_handler(settings: Settings) -> JWTHandler:
    return JWTHandler(settings)


def test_generate_access_token(jwt_handler: JWTHandler, settings: Settings) -> None:
    user_id = uuid4()
    token = jwt_handler.generate_access_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify claims
    payload = jwt_handler.validate_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["iss"] == settings.APP_NAME
    assert payload["type"] == "access"


def test_generate_refresh_token(jwt_handler: JWTHandler, settings: Settings) -> None:
    user_id = uuid4()
    token = jwt_handler.generate_refresh_token(user_id)
    payload = jwt_handler.validate_refresh_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"


def test_refresh_token_expires_longer(jwt_handler: JWTHandler, settings: Settings) -> None:
    """Refresh token expiry should be significantly longer than access token."""
    access_payload = jwt_handler.validate_access_token(jwt_handler.generate_access_token(uuid4()))
    refresh_payload = jwt_handler.validate_refresh_token(jwt_handler.generate_refresh_token(uuid4()))
    access_delta = access_payload["exp"] - access_payload["iat"]
    refresh_delta = refresh_payload["exp"] - refresh_payload["iat"]
    assert refresh_delta > access_delta * 10  # 30 days vs 15 minutes


def test_access_token_is_not_refresh(jwt_handler: JWTHandler) -> None:
    access_token = jwt_handler.generate_access_token(uuid4())
    with pytest.raises(JWTError):
        jwt_handler.validate_refresh_token(access_token)


def test_refresh_token_is_not_access(jwt_handler: JWTHandler) -> None:
    refresh_token = jwt_handler.generate_refresh_token(uuid4())
    with pytest.raises(JWTError):
        jwt_handler.validate_access_token(refresh_token)
