"""Unit tests for RefreshTokenUseCase."""

import asyncio
from pathlib import Path
from tempfile import mkdtemp
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from backend.application.use_cases.refresh_token import RefreshTokenUseCase
from backend.infrastructure.auth.jwt_handler import JWTHandler
from backend.config.settings import Settings


def _gen_keys() -> tuple[Path, Path]:
    """Generate temporary RSA key pair."""
    pk = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    tmp = Path(mkdtemp())
    p = tmp / "private.pem"
    pub = tmp / "public.pem"
    p.write_bytes(pk.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))
    pub.write_bytes(pk.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))
    return p, pub


@pytest.fixture
def jwt_keys() -> tuple[Path, Path]:
    return _gen_keys()


@pytest.fixture
def settings(jwt_keys: tuple[Path, Path]):
    return Settings(
        APP_NAME="TestApp",
        JWT_PRIVATE_KEY=jwt_keys[0],
        JWT_PUBLIC_KEY=jwt_keys[1],
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15,
        JWT_REFRESH_TOKEN_EXPIRE_DAYS=30,
    )


@pytest.fixture
def jwt_handler(settings: Settings) -> JWTHandler:
    return JWTHandler(settings)


@pytest.fixture
def refresh_use_case(jwt_handler: JWTHandler) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(jwt_handler)


async def test_generate_refresh_token(refresh_use_case: RefreshTokenUseCase) -> None:
    """Test refresh token generation."""
    token = refresh_use_case.generate_refresh_token(uuid4())
    assert isinstance(token, str)
    assert len(token) > 0


async def test_refresh_returns_new_tokens(refresh_use_case: RefreshTokenUseCase) -> None:
    """Test refresh returns new access and refresh tokens."""
    user_id = uuid4()
    refresh_token = refresh_use_case.generate_refresh_token(user_id)
    await asyncio.sleep(1.1)  # ensure new refresh token has different iat
    result = await refresh_use_case.refresh(refresh_token)

    assert "access_token" in result
    assert "refresh_token" in result
    assert result["access_token"] != refresh_token
    assert result["refresh_token"] != refresh_token
