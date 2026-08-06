"""Google OAuth handler — validates ID tokens and extracts user info."""

import httpx
from pydantic import BaseModel


class GoogleUserInfo(BaseModel):
    """User info extracted from Google ID token."""

    sub: str  # Google user ID
    email: str
    email_verified: bool = True


class GoogleOAuthHandler:
    """Handles Google OAuth ID Token validation."""

    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_ISSUER = "https://accounts.google.com"
    GOOGLE_ISSUER_HD = "accounts.google.com"

    def __init__(self, client_id: str, client_secret: str = ""):
        self._client_id = client_id
        self._client_secret = client_secret

    async def validate_id_token(self, id_token: str) -> GoogleUserInfo:
        """Validate a Google ID token and return user info.

        Raises ValueError on validation failure.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                self.GOOGLE_TOKEN_INFO_URL,
                params={"id_token": id_token},
            )

            if response.status_code != 200:
                raise ValueError(f"Invalid ID token: HTTP {response.status_code}")

            data = response.json()

            # Validate issuer
            iss = data.get("iss")
            if iss not in (self.GOOGLE_ISSUER, self.GOOGLE_ISSUER_HD):
                raise ValueError(f"Invalid issuer: {iss}")

            # Validate audience (client_id)
            aud = data.get("aud")
            if aud != self._client_id:
                raise ValueError(f"Audience mismatch: expected {self._client_id}, got {aud}")

            return GoogleUserInfo(
                sub=data["sub"],
                email=data["email"],
                email_verified=data.get("email_verified", True),
            )

    async def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict:
        """Exchange an authorization code for Google user info.

        This is an alternative flow that uses the code grant endpoint.
        Returns raw token response dict.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            response.raise_for_status()
            return response.json()
