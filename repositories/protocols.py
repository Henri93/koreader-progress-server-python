from typing import Protocol, Optional
from dataclasses import dataclass


@dataclass
class UserEntity:
    """Database-agnostic user representation."""
    id: str  # String to support both int IDs and DynamoDB string keys
    username: str
    password_hash: str


@dataclass
class ProgressEntity:
    """Database-agnostic progress representation."""
    user_id: str
    document: str
    progress: str
    percentage: float
    device: str
    device_id: str
    timestamp: int


class UserRepository(Protocol):
    """Protocol for user data access."""

    def get_by_username(self, username: str) -> Optional[UserEntity]:
        """Retrieve user by username."""
        ...

    def create(self, username: str, password_hash: str) -> UserEntity:
        """Create a new user. Raises ValueError if username exists."""
        ...

    def exists(self, username: str) -> bool:
        """Check if username is taken."""
        ...


class ProgressRepository(Protocol):
    """Protocol for progress data access."""

    def get_by_user_and_document(
        self, user_id: str, document: str
    ) -> Optional[ProgressEntity]:
        """Get progress for a specific user and document."""
        ...

    def upsert(self, progress: ProgressEntity) -> ProgressEntity:
        """Insert or update progress record."""
        ...
