"""Domain interfaces — ports that infrastructure implements."""

from backend.domain.interfaces.i_llm_config_repository import ILlmConfigRepository
from backend.domain.interfaces.i_user_repository import IUserRepository

__all__ = [
    "IUserRepository",
    "ILlmConfigRepository",
]
