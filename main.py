import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException

from schemas import UserCreate, ProgressUpdate, ProgressResponse, LinkRequest, LinkResponse, DocumentLinkResponse
from repositories import get_user_repository, get_progress_repository, get_document_link_repository
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
    link_repo=Depends(get_document_link_repository),
):
    if not all([
        progress_data.document,
        progress_data.progress,
        progress_data.percentage is not None,
        progress_data.device,
        progress_data.device_id,
    ]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    document_hash = progress_data.document
    canonical_hash = document_hash

    # Check if this document hash already has a link
    existing_canonical = link_repo.get_canonical(user.id, document_hash)
    if existing_canonical:
        canonical_hash = existing_canonical
    elif progress_data.filename:
        # Auto-link: find ALL documents with the same filename and link them together
        all_with_filename = progress_repo.get_all_by_user_and_filename(user.id, progress_data.filename)

        if all_with_filename:
            # Use the first existing document as the canonical (the oldest one)
            # This ensures consistency - the canonical doesn't change
            canonical_hash = min(all_with_filename, key=lambda p: p.timestamp).document

            # Link all documents (including the current one) to the canonical
            for p in all_with_filename:
                if p.document != canonical_hash:
                    existing_link = link_repo.get_canonical(user.id, p.document)
                    if not existing_link:
                        link_repo.create_link(user.id, p.document, canonical_hash)

            # Also link the current document if it's different from canonical
            if document_hash != canonical_hash:
                existing_link = link_repo.get_canonical(user.id, document_hash)
                if not existing_link:
                    link_repo.create_link(user.id, document_hash, canonical_hash)

    progress_entity = ProgressEntity(
        user_id=user.id,
        document=canonical_hash,
        progress=progress_data.progress,
        percentage=progress_data.percentage,
        device=progress_data.device,
        device_id=progress_data.device_id,
        timestamp=int(time.time()),
        filename=progress_data.filename,
    )

    progress_repo.upsert(progress_entity)
    return {"status": "success"}


@app.get("/syncs/progress/{document}")
def get_progress(
    document: str,
    user: UserEntity = Depends(get_current_user),
    progress_repo=Depends(get_progress_repository),
    link_repo=Depends(get_document_link_repository),
):
    # Resolve canonical hash if this document is linked
    canonical_hash = link_repo.get_canonical(user.id, document)
    lookup_hash = canonical_hash if canonical_hash else document

    progress = progress_repo.get_by_user_and_document(user.id, lookup_hash)

    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found")

    return ProgressResponse(
        document=progress.document,
        progress=progress.progress,
        percentage=progress.percentage,
        device=progress.device,
        device_id=progress.device_id,
        timestamp=progress.timestamp,
        filename=progress.filename,
    )


@app.post("/documents/link", status_code=201)
def link_documents(
    link_request: LinkRequest,
    user: UserEntity = Depends(get_current_user),
    progress_repo=Depends(get_progress_repository),
    link_repo=Depends(get_document_link_repository),
):
    if len(link_request.hashes) < 2:
        raise HTTPException(status_code=400, detail="At least 2 hashes required to create a link")

    # Find the canonical hash: the first one with existing progress, or the first one
    canonical_hash = None
    for h in link_request.hashes:
        progress = progress_repo.get_by_user_and_document(user.id, h)
        if progress:
            canonical_hash = h
            break

    if not canonical_hash:
        canonical_hash = link_request.hashes[0]

    # Create links for all other hashes
    linked = []
    for h in link_request.hashes:
        if h != canonical_hash:
            # Check if this hash already has a different canonical
            existing = link_repo.get_canonical(user.id, h)
            if existing and existing != canonical_hash:
                # Update the link to point to the new canonical
                link_repo.delete_link(user.id, h)
            link_repo.create_link(user.id, h, canonical_hash)
            linked.append(h)

    return LinkResponse(canonical=canonical_hash, linked=linked)


@app.get("/documents/links")
def list_document_links(
    user: UserEntity = Depends(get_current_user),
    link_repo=Depends(get_document_link_repository),
):
    links = link_repo.get_all_links(user.id)
    return [
        DocumentLinkResponse(
            document_hash=link.document_hash,
            canonical_hash=link.canonical_hash
        )
        for link in links
    ]


@app.delete("/documents/link/{document_hash}")
def unlink_document(
    document_hash: str,
    user: UserEntity = Depends(get_current_user),
    link_repo=Depends(get_document_link_repository),
):
    deleted = link_repo.delete_link(user.id, document_hash)
    if not deleted:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"status": "success"}
