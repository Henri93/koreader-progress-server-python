from typing import Optional
from sqlalchemy.orm import Session
from models import User, Progress
from repositories.protocols import UserEntity, ProgressEntity


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
            timestamp=progress.timestamp
        )

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
        else:
            db_progress = Progress(
                user_id=int(progress.user_id),
                document=progress.document,
                progress=progress.progress,
                percentage=progress.percentage,
                device=progress.device,
                device_id=progress.device_id,
                timestamp=progress.timestamp
            )
            self.db.add(db_progress)

        self.db.commit()
        return progress
