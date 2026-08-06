"""Unit tests for GoogleOAuthHandler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.infrastructure.auth.google_oauth import GoogleOAuthHandler, GoogleUserInfo


@pytest.fixture
def handler() -> GoogleOAuthHandler:
    return GoogleOAuthHandler(client_id="test-client-id")


async def test_validate_id_token_success(handler: GoogleOAuthHandler) -> None:
    """Test successful ID token validation."""
    fake_token = "fake.jwt.token"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sub": "google-user-123",
        "email": "user@example.com",
        "email_verified": True,
        "iss": "https://accounts.google.com",
        "aud": "test-client-id",
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("backend.infrastructure.auth.google_oauth.httpx.AsyncClient", return_value=mock_client):
        result = await handler.validate_id_token(fake_token)

    assert isinstance(result, GoogleUserInfo)
    assert result.sub == "google-user-123"
    assert result.email == "user@example.com"
    assert result.email_verified is True


async def test_validate_id_token_bad_issuer(handler: GoogleOAuthHandler) -> None:
    """Test ID token validation with bad issuer."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sub": "google-user-123",
        "email": "user@example.com",
        "iss": "https://evil.com",
        "aud": "test-client-id",
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("backend.infrastructure.auth.google_oauth.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ValueError, match="Invalid issuer"):
            await handler.validate_id_token("fake-token")


async def test_validate_id_token_bad_audience(handler: GoogleOAuthHandler) -> None:
    """Test ID token validation with bad audience."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sub": "google-user-123",
        "email": "user@example.com",
        "iss": "https://accounts.google.com",
        "aud": "wrong-client-id",
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("backend.infrastructure.auth.google_oauth.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ValueError, match="Audience mismatch"):
            await handler.validate_id_token("fake-token")


async def test_validate_id_token_http_error(handler: GoogleOAuthHandler) -> None:
    """Test ID token validation with HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("backend.infrastructure.auth.google_oauth.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(ValueError, match="Invalid ID token"):
            await handler.validate_id_token("bad-token")
