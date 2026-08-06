"""Google OAuth use case — orchestrates the OAuth flow."""

import logging
from uuid import UUID, uuid4

from backend.application.use_cases.refresh_token import RefreshTokenUseCase
from backend.domain.entities.user import User
from backend.domain.interfaces.i_user_repository import IUserRepository
from backend.domain.value_objects.role import Role
from backend.infrastructure.auth.google_oauth import GoogleOAuthHandler
from backend.infrastructure.auth.jwt_handler import JWTHandler

logger = logging.getLogger(__name__)


class GoogleOAuthUseCase:
    """Handle Google OAuth login: validate ID token → create/update user → issue JWT."""

    def __init__(
        self,
        user_repository: IUserRepository,
        jwt_handler: JWTHandler,
        google_handler: GoogleOAuthHandler,
        refresh_use_case: RefreshTokenUseCase,
    ):
        self._user_repo = user_repository
        self._jwt = jwt_handler
        self._google = google_handler
        self._refresh = refresh_use_case

    async def authenticate(self, id_token: str) -> dict:
        """Authenticate with Google ID token.

        Returns dict with:
            - access_token: JWT access token
            - refresh_token: JWT refresh token (also set as cookie)
            - user: User entity
        """
        # 1. Validate Google ID token and extract user info
        google_user = await self._google.validate_id_token(id_token)
        logger.info("Google auth for email=%s (google_id=%s)", google_user.email, google_user.sub)

        # 2. Look up or create user
        user = await self._user_repo.get_by_google_id(google_user.sub)
        if user is None:
            # First login — create user
            user = User(
                id=uuid4(),
                google_id=google_user.sub,
                email=google_user.email,
                role=Role.USER,
                is_blocked=False,
                default_llm_config_id=None,
            )
            user = await self._user_repo.create(user)
            logger.info("New user created: %s", user.email)
        else:
            # Existing user — update email if changed
            user.email = google_user.email
            user = await self._user_repo.update(user)
            logger.info("Existing user updated: %s", user.email)

        # 3. Generate tokens
        access_token = self._jwt.generate_access_token(user.id)
        refresh_token = self._refresh.generate_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user,
        }
