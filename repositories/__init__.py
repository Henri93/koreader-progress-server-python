import os
from typing import Generator

from repositories.protocols import UserRepository, ProgressRepository, DocumentLinkRepository

DB_BACKEND = os.getenv("DB_BACKEND", "sql")


def get_user_repository() -> Generator[UserRepository, None, None]:
    """Factory for user repository based on DB_BACKEND environment variable."""
    if DB_BACKEND == "dynamodb":
        from repositories.dynamodb import DynamoUserRepository
        yield DynamoUserRepository()
    else:
        from database import get_db
        from repositories.sql import SQLUserRepository
        db = next(get_db())
        try:
            yield SQLUserRepository(db)
        finally:
            db.close()


def get_progress_repository() -> Generator[ProgressRepository, None, None]:
    """Factory for progress repository based on DB_BACKEND environment variable."""
    if DB_BACKEND == "dynamodb":
        from repositories.dynamodb import DynamoProgressRepository
        yield DynamoProgressRepository()
    else:
        from database import get_db
        from repositories.sql import SQLProgressRepository
        db = next(get_db())
        try:
            yield SQLProgressRepository(db)
        finally:
            db.close()


def get_document_link_repository() -> Generator[DocumentLinkRepository, None, None]:
    """Factory for document link repository based on DB_BACKEND environment variable."""
    if DB_BACKEND == "dynamodb":
        from repositories.dynamodb import DynamoDocumentLinkRepository
        yield DynamoDocumentLinkRepository()
    else:
        from database import get_db
        from repositories.sql import SQLDocumentLinkRepository
        db = next(get_db())
        try:
            yield SQLDocumentLinkRepository(db)
        finally:
            db.close()
