"""Domain layer — pure Python entities, value objects, and interfaces."""

from backend.domain.entities.user import User
from backend.domain.interfaces.i_user_repository import IUserRepository
from backend.domain.value_objects.role import Role

__all__ = [
    "IUserRepository",
    "Role",
    "User",
]
