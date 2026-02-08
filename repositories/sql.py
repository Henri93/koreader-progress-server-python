from typing import Optional
from sqlalchemy.orm import Session
from models import User, Progress, DocumentLink
from repositories.protocols import UserEntity, ProgressEntity, DocumentLinkEntity


class SQLUserRepository:
    """SQLAlchemy-based user repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> Optional[UserEntity]:
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        return UserEntity(
            id=str(user.id),
            username=user.username,
            password_hash=user.password_hash
        )

    def create(self, username: str, password_hash: str) -> UserEntity:
        db_user = User(username=username, password_hash=password_hash)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return UserEntity(
            id=str(db_user.id),
            username=db_user.username,
            password_hash=db_user.password_hash
        )

    def exists(self, username: str) -> bool:
        return self.db.query(User).filter(User.username == username).first() is not None


class SQLProgressRepository:
    """SQLAlchemy-based progress repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_document(
        self, user_id: str, document: str
    ) -> Optional[ProgressEntity]:
        progress = (
            self.db.query(Progress)
            .filter(Progress.user_id == int(user_id), Progress.document == document)
            .order_by(Progress.timestamp.desc())
            .first()
        )
        if not progress:
            return None
        return ProgressEntity(
            user_id=str(progress.user_id),
            document=progress.document,
            progress=progress.progress,
            percentage=progress.percentage,
            device=progress.device,
            device_id=progress.device_id,
            timestamp=progress.timestamp,
            filename=progress.filename
        )

    def get_by_user_and_filename(
        self, user_id: str, filename: str
    ) -> Optional[ProgressEntity]:
        progress = (
            self.db.query(Progress)
            .filter(Progress.user_id == int(user_id), Progress.filename == filename)
            .order_by(Progress.timestamp.desc())
            .first()
        )
        if not progress:
            return None
        return ProgressEntity(
            user_id=str(progress.user_id),
            document=progress.document,
            progress=progress.progress,
            percentage=progress.percentage,
            device=progress.device,
            device_id=progress.device_id,
            timestamp=progress.timestamp,
            filename=progress.filename
        )

    def get_all_by_user_and_filename(
        self, user_id: str, filename: str
    ) -> list[ProgressEntity]:
        records = (
            self.db.query(Progress)
            .filter(Progress.user_id == int(user_id), Progress.filename == filename)
            .all()
        )
        return [
            ProgressEntity(
                user_id=str(p.user_id),
                document=p.document,
                progress=p.progress,
                percentage=p.percentage,
                device=p.device,
                device_id=p.device_id,
                timestamp=p.timestamp,
                filename=p.filename
            )
            for p in records
        ]

    def upsert(self, progress: ProgressEntity) -> ProgressEntity:
        existing = (
            self.db.query(Progress)
            .filter(
                Progress.user_id == int(progress.user_id),
                Progress.document == progress.document
            )
            .first()
        )

        if existing:
            existing.progress = progress.progress
            existing.percentage = progress.percentage
            existing.device = progress.device
            existing.device_id = progress.device_id
            existing.timestamp = progress.timestamp
            if progress.filename:
                existing.filename = progress.filename
        else:
            db_progress = Progress(
                user_id=int(progress.user_id),
                document=progress.document,
                progress=progress.progress,
                percentage=progress.percentage,
                device=progress.device,
                device_id=progress.device_id,
                timestamp=progress.timestamp,
                filename=progress.filename
            )
            self.db.add(db_progress)

        self.db.commit()
        return progress


class SQLDocumentLinkRepository:
    """SQLAlchemy-based document link repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_canonical(self, user_id: str, document_hash: str) -> Optional[str]:
        link = (
            self.db.query(DocumentLink)
            .filter(
                DocumentLink.user_id == int(user_id),
                DocumentLink.document_hash == document_hash
            )
            .first()
        )
        return link.canonical_hash if link else None

    def create_link(self, user_id: str, document_hash: str, canonical_hash: str) -> DocumentLinkEntity:
        db_link = DocumentLink(
            user_id=int(user_id),
            document_hash=document_hash,
            canonical_hash=canonical_hash
        )
        self.db.add(db_link)
        self.db.commit()
        return DocumentLinkEntity(
            user_id=user_id,
            document_hash=document_hash,
            canonical_hash=canonical_hash
        )

    def get_all_links(self, user_id: str) -> list[DocumentLinkEntity]:
        links = (
            self.db.query(DocumentLink)
            .filter(DocumentLink.user_id == int(user_id))
            .all()
        )
        return [
            DocumentLinkEntity(
                user_id=str(link.user_id),
                document_hash=link.document_hash,
                canonical_hash=link.canonical_hash
            )
            for link in links
        ]

    def delete_link(self, user_id: str, document_hash: str) -> bool:
        result = (
            self.db.query(DocumentLink)
            .filter(
                DocumentLink.user_id == int(user_id),
                DocumentLink.document_hash == document_hash
            )
            .delete()
        )
        self.db.commit()
        return result > 0

    def get_linked_hashes(self, user_id: str, canonical_hash: str) -> list[str]:
        links = (
            self.db.query(DocumentLink)
            .filter(
                DocumentLink.user_id == int(user_id),
                DocumentLink.canonical_hash == canonical_hash
            )
            .all()
        )
        return [link.document_hash for link in links]
