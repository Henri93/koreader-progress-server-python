import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException

from schemas import UserCreate, ProgressUpdate, ProgressResponse
from repositories import get_user_repository, get_progress_repository
from repositories.protocols import UserEntity, ProgressEntity
from auth import hash_password, get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Only initialize SQL database if using SQL backend
    if os.getenv("DB_BACKEND", "sql") == "sql":
        from database import init_db
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
def create_user(user: UserCreate, user_repo=Depends(get_user_repository)):
    if not user.username or not user.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    if user_repo.exists(user.username):
        raise HTTPException(status_code=402, detail="Username already exists")

    # KOReader sends password as MD5 hash during registration, so don't double-hash
    user_repo.create(user.username, hash_password(user.password))

    return {"status": "success"}


@app.get("/users/auth")
def auth_user(user: UserEntity = Depends(get_current_user)):
    return {"status": "authenticated"}


@app.put("/syncs/progress")
def update_progress(
    progress_data: ProgressUpdate,
    user: UserEntity = Depends(get_current_user),
    progress_repo=Depends(get_progress_repository),
):
    if not all([
        progress_data.document,
        progress_data.progress,
        progress_data.percentage is not None,
        progress_data.device,
        progress_data.device_id,
    ]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    progress_entity = ProgressEntity(
        user_id=user.id,
        document=progress_data.document,
        progress=progress_data.progress,
        percentage=progress_data.percentage,
        device=progress_data.device,
        device_id=progress_data.device_id,
        timestamp=int(time.time()),
    )

    progress_repo.upsert(progress_entity)
    return {"status": "success"}


@app.get("/syncs/progress/{document}")
def get_progress(
    document: str,
    user: UserEntity = Depends(get_current_user),
    progress_repo=Depends(get_progress_repository),
):
    progress = progress_repo.get_by_user_and_document(user.id, document)

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
