"""Domain value objects — pure Python, no external dependencies."""

from enum import Enum


class Role(str, Enum):
    """User roles."""

    USER = "USER"
    ADMIN = "ADMIN"
