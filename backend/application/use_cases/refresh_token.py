"""Refresh token use case — validate and issue new access token."""

import logging
from uuid import UUID

from backend.infrastructure.auth.jwt_handler import JWTHandler

logger = logging.getLogger(__name__)


class RefreshTokenUseCase:
    """Handle refresh token operations."""

    def __init__(self, jwt_handler: JWTHandler):
        self._jwt = jwt_handler

    def generate_refresh_token(self, user_id: UUID) -> str:
        """Generate a new refresh token."""
        return self._jwt.generate_refresh_token(user_id)

    async def refresh(self, refresh_token: str) -> dict:
        """Validate refresh token and issue new access token.

        Returns dict with:
            - access_token: new JWT access token
            - refresh_token: new refresh token (rotated)
        """
        # Validate refresh token
        payload = self._jwt.validate_refresh_token(refresh_token)
        user_id = UUID(payload["sub"])

        # Issue new tokens
        access_token = self._jwt.generate_access_token(user_id)
        new_refresh_token = self._jwt.generate_refresh_token(user_id)

        logger.info("Token refreshed for user %s", user_id)
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
        }
