"""Unit tests for GoogleOAuthUseCase."""

from pathlib import Path
from tempfile import mkdtemp
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from backend.application.use_cases.google_oauth import GoogleOAuthUseCase
from backend.application.use_cases.refresh_token import RefreshTokenUseCase
from backend.domain.entities.user import User
from backend.domain.value_objects.role import Role
from backend.infrastructure.auth.google_oauth import GoogleUserInfo, GoogleOAuthHandler
from backend.infrastructure.auth.jwt_handler import JWTHandler
from backend.infrastructure.repositories.fake_user_repository import FakeUserRepository
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
    )


@pytest.fixture
def jwt_handler(settings: Settings) -> JWTHandler:
    return JWTHandler(settings)


@pytest.fixture
def refresh_use_case(jwt_handler: JWTHandler) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(jwt_handler)


@pytest.fixture
def fake_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def google_handler() -> GoogleOAuthHandler:
    from backend.infrastructure.auth.google_oauth import GoogleOAuthHandler
    return GoogleOAuthHandler(client_id="test-client")


@pytest.fixture
def use_case(
    fake_repo: FakeUserRepository,
    jwt_handler: JWTHandler,
    google_handler: GoogleOAuthHandler,
    refresh_use_case: RefreshTokenUseCase,
) -> GoogleOAuthUseCase:
    return GoogleOAuthUseCase(fake_repo, jwt_handler, google_handler, refresh_use_case)


async def test_authenticate_new_user(
    use_case: GoogleOAuthUseCase,
    fake_repo: FakeUserRepository,
) -> None:
    """Test authentication creates a new user."""
    mock_google_user = GoogleUserInfo(
        sub="google-new-user",
        email="new@example.com",
        email_verified=True,
    )

    # Patch validate_id_token
    use_case._google.validate_id_token = AsyncMock(return_value=mock_google_user)
    use_case._user_repo.get_by_google_id = AsyncMock(return_value=None)

    result = await use_case.authenticate("fake-id-token")

    assert "access_token" in result
    assert "refresh_token" in result
    assert result["user"].email == "new@example.com"
    assert result["user"].google_id == "google-new-user"
    assert result["user"].role == Role.USER


async def test_authenticate_existing_user(
    use_case: GoogleOAuthUseCase,
    fake_repo: FakeUserRepository,
) -> None:
    """Test authentication updates an existing user."""
    existing_user = User(
        id=uuid4(),
        google_id="google-existing",
        email="old@example.com",
    )
    mock_google_user = GoogleUserInfo(
        sub="google-existing",
        email="new@example.com",
    )

    use_case._google.validate_id_token = AsyncMock(return_value=mock_google_user)
    use_case._user_repo.get_by_google_id = AsyncMock(return_value=existing_user)

    result = await use_case.authenticate("fake-id-token")

    assert result["user"].email == "new@example.com"  # email updated


async def test_authenticate_returns_tokens(
    use_case: GoogleOAuthUseCase,
) -> None:
    """Test that authentication returns valid JWT tokens."""
    mock_google_user = GoogleUserInfo(sub="google-123", email="user@example.com")
    use_case._google.validate_id_token = AsyncMock(return_value=mock_google_user)
    use_case._user_repo.get_by_google_id = AsyncMock(return_value=None)

    result = await use_case.authenticate("fake-token")

    # Verify access token is valid
    access_payload = use_case._jwt.validate_access_token(result["access_token"])
    assert access_payload["type"] == "access"

    # Verify refresh token is valid
    refresh_payload = use_case._jwt.validate_refresh_token(result["refresh_token"])
    assert refresh_payload["type"] == "refresh"
