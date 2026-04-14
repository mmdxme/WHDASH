"""
Repositories Package
=====================
Data access layer for the platform.

Base:
- base_repository: Base class with common query patterns

User Repository:
- user_repository: User data access operations
"""

from .base_repository import BaseRepository

__all__ = [
    'BaseRepository',
]
