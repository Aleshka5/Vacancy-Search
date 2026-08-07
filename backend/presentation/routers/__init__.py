"""Presentation routers."""

from backend.presentation.routers.admin import router as admin_router
from backend.presentation.routers.auth import router as auth_router
from backend.presentation.routers.llm_config import router as llm_config_router

__all__ = [
    "admin_router",
    "auth_router",
    "llm_config_router",
]
