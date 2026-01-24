import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, init_db
from models import User, Progress, UserCreate, ProgressUpdate, ProgressResponse
from auth import hash_password, md5_hash, get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="KOReader Sync Server", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthcheck")
def healthcheck():
    return {"state": "OK"}


@app.post("/users/create", status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if not user.username or not user.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=402, detail="Username already exists")

    db_user = User(username=user.username, password_hash=hash_password(md5_hash(user.password)))
    db.add(db_user)
    db.commit()

    return {"status": "success"}


@app.get("/users/auth")
def auth_user(user: User = Depends(get_current_user)):
    return {"status": "authenticated"}


@app.put("/syncs/progress")
def update_progress(
    progress_data: ProgressUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not all([
        progress_data.document,
        progress_data.progress,
        progress_data.percentage is not None,
        progress_data.device,
        progress_data.device_id,
    ]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    existing = (
        db.query(Progress)
        .filter(Progress.user_id == user.id, Progress.document == progress_data.document)
        .first()
    )

    if existing:
        existing.progress = progress_data.progress
        existing.percentage = progress_data.percentage
        existing.device = progress_data.device
        existing.device_id = progress_data.device_id
        existing.timestamp = int(time.time())
    else:
        db_progress = Progress(
            user_id=user.id,
            document=progress_data.document,
            progress=progress_data.progress,
            percentage=progress_data.percentage,
            device=progress_data.device,
            device_id=progress_data.device_id,
        )
        db.add(db_progress)

    db.commit()
    return {"status": "success"}


@app.get("/syncs/progress/{document}")
def get_progress(
    document: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    progress = (
        db.query(Progress)
        .filter(Progress.user_id == user.id, Progress.document == document)
        .order_by(Progress.timestamp.desc())
        .first()
    )

    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    return ProgressResponse(
        document=progress.document,
        progress=progress.progress,
        percentage=progress.percentage,
        device=progress.device,
        device_id=progress.device_id,
        timestamp=progress.timestamp,
    )
