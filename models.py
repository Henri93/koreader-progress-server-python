import time
from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from pydantic import BaseModel
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document = Column(String, index=True, nullable=False)
    progress = Column(String, nullable=False)
    percentage = Column(Float, nullable=False)
    device = Column(String, nullable=False)
    device_id = Column(String, nullable=False)
    timestamp = Column(Integer, default=lambda: int(time.time()))
    filename = Column(String, nullable=True, index=True)


class DocumentLink(Base):
    __tablename__ = "document_links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_hash = Column(String, nullable=False, index=True)
    canonical_hash = Column(String, nullable=False)


class BookLabel(Base):
    __tablename__ = "book_labels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    canonical_hash = Column(String, nullable=False, index=True)
    label = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'canonical_hash', name='uq_user_canonical'),
    )


class UserCreate(BaseModel):
    username: str
    password: str


class ProgressUpdate(BaseModel):
    document: str
    progress: str
    percentage: float
    device: str
    device_id: str


class ProgressResponse(BaseModel):
    document: str
    progress: str
    percentage: float
    device: str
    device_id: str
    timestamp: int
