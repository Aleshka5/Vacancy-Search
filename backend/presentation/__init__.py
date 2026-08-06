"""Presentation layer — FastAPI routers, schemas, dependencies."""

from backend.presentation.dependencies import get_current_user
from backend.presentation.routers.auth import router as auth_router

__all__ = [
    "auth_router",
    "get_current_user",
]
