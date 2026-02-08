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
