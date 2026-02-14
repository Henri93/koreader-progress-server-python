from typing import Optional
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class ProgressUpdate(BaseModel):
    document: str
    progress: str
    percentage: float
    device: str
    device_id: str
    filename: Optional[str] = None


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
