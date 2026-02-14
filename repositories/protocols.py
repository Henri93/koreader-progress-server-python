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
    filename: Optional[str] = None


@dataclass
class DocumentLinkEntity:
    """Database-agnostic document link representation."""
    user_id: str
    document_hash: str
    canonical_hash: str


@dataclass
class BookLabelEntity:
    """Database-agnostic book label representation."""
    user_id: str
    canonical_hash: str
    label: str


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

    def get_by_user_and_filename(
        self, user_id: str, filename: str
    ) -> Optional[ProgressEntity]:
        """Get progress for a specific user and filename."""
        ...

    def get_all_by_user_and_filename(
        self, user_id: str, filename: str
    ) -> list[ProgressEntity]:
        """Get all progress records for a specific user and filename."""
        ...

    def upsert(self, progress: ProgressEntity) -> ProgressEntity:
        """Insert or update progress record."""
        ...

    def get_all_by_user(self, user_id: str) -> list[ProgressEntity]:
        """Get all progress records for a user."""
        ...


class DocumentLinkRepository(Protocol):
    """Protocol for document link data access."""

    def get_canonical(self, user_id: str, document_hash: str) -> Optional[str]:
        """Get canonical hash for a document hash. Returns None if no link exists."""
        ...

    def create_link(self, user_id: str, document_hash: str, canonical_hash: str) -> DocumentLinkEntity:
        """Create a link from document_hash to canonical_hash."""
        ...

    def get_all_links(self, user_id: str) -> list[DocumentLinkEntity]:
        """Get all document links for a user."""
        ...

    def delete_link(self, user_id: str, document_hash: str) -> bool:
        """Delete a link. Returns True if deleted, False if not found."""
        ...

    def get_linked_hashes(self, user_id: str, canonical_hash: str) -> list[str]:
        """Get all hashes linked to a canonical hash."""
        ...


class BookLabelRepository(Protocol):
    """Protocol for book label data access."""

    def get_label(self, user_id: str, canonical_hash: str) -> Optional[str]:
        """Get label for a canonical hash. Returns None if no label exists."""
        ...

    def set_label(self, user_id: str, canonical_hash: str, label: str) -> BookLabelEntity:
        """Set or update label for a canonical hash."""
        ...

    def delete_label(self, user_id: str, canonical_hash: str) -> bool:
        """Delete a label. Returns True if deleted, False if not found."""
        ...

    def get_all_labels(self, user_id: str) -> list[BookLabelEntity]:
        """Get all labels for a user."""
        ...
