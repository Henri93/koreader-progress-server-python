from typing import Optional
from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or len(v) < 1:
            raise ValueError('Username is required')
        if len(v) > 64:
            raise ValueError('Username too long (max 64 characters)')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or len(v) < 1:
            raise ValueError('Password is required')
        if len(v) > 128:
            raise ValueError('Password too long (max 128 characters)')
        return v


class ProgressUpdate(BaseModel):
    document: str
    progress: str
    percentage: float
    device: str
    device_id: str
    filename: Optional[str] = None

    @field_validator('percentage')
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError('Percentage must be between 0 and 1')
        return v

    @field_validator('document')
    @classmethod
    def validate_document(cls, v: str) -> str:
        if not v or len(v) > 256:
            raise ValueError('Document hash must be 1-256 characters')
        return v


class ProgressResponse(BaseModel):
    document: str
    progress: str
    percentage: float
    device: str
    device_id: str
    timestamp: int
    filename: Optional[str] = None


class LinkRequest(BaseModel):
    hashes: list[str]


class LinkResponse(BaseModel):
    canonical: str
    linked: list[str]


class DocumentLinkResponse(BaseModel):
    document_hash: str
    canonical_hash: str


class BookSummary(BaseModel):
    """Summary of a book for the frontend."""
    canonical_hash: str
    linked_hashes: list[str]
    label: Optional[str] = None
    filename: Optional[str] = None
    progress: str
    percentage: float
    device: str
    device_id: str
    timestamp: int


class BooksListResponse(BaseModel):
    """Response for list all books endpoint."""
    books: list[BookSummary]


class BookLabelUpdate(BaseModel):
    """Request to update a book's label."""
    canonical_hash: str
    label: str


class BookLabelResponse(BaseModel):
    """Response after updating a book's label."""
    canonical_hash: str
    label: str
