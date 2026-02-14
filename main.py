import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import Response
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from schemas import (
    UserCreate, ProgressUpdate, ProgressResponse, LinkRequest, LinkResponse,
    DocumentLinkResponse, BookSummary, BooksListResponse, BookLabelUpdate, BookLabelResponse
)
from repositories import get_user_repository, get_progress_repository, get_document_link_repository, get_book_label_repository
from svg_card import render_progress_card
from repositories.protocols import UserEntity, ProgressEntity
from auth import hash_password, get_current_user


# Rate limiter - disabled in test mode
_rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
limiter = Limiter(key_func=get_remote_address, enabled=_rate_limit_enabled)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Only initialize SQL database if using SQL backend
    if os.getenv("DB_BACKEND", "sql") == "sql":
        from database import init_db
        init_db()
    yield


app = FastAPI(title="KOReader Sync Server", lifespan=lifespan)
app.state.limiter = limiter
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return Response(
        content='{"detail": "Rate limit exceeded"}',
        status_code=429,
        media_type="application/json"
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Return 400 Bad Request for validation errors (KOReader compatibility)
    return Response(
        content='{"detail": "Invalid request data"}',
        status_code=400,
        media_type="application/json"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/healthcheck")
def healthcheck():
    return {"state": "OK"}


@app.post("/users/create", status_code=201)
@limiter.limit("5/minute")
def create_user(request: Request, user: UserCreate, user_repo=Depends(get_user_repository)):
    if user_repo.exists(user.username):
        raise HTTPException(status_code=402, detail="Username already exists")

    # KOReader sends password as MD5 hash during registration, so don't double-hash
    user_repo.create(user.username, hash_password(user.password))

    return {"status": "success"}


@app.get("/users/auth")
@limiter.limit("10/minute")
def auth_user(request: Request, user: UserEntity = Depends(get_current_user)):
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


@app.get("/books")
def list_books(
    limit: int = 50,
    offset: int = 0,
    user: UserEntity = Depends(get_current_user),
    progress_repo=Depends(get_progress_repository),
    link_repo=Depends(get_document_link_repository),
    label_repo=Depends(get_book_label_repository),
) -> BooksListResponse:
    """List all books with their progress for the authenticated user."""
    all_progress = progress_repo.get_all_by_user(user.id)
    all_links = link_repo.get_all_links(user.id)
    all_labels = label_repo.get_all_labels(user.id)

    label_map = {label.canonical_hash: label.label for label in all_labels}
    reverse_link_map: dict[str, list[str]] = {}
    for link in all_links:
        if link.canonical_hash not in reverse_link_map:
            reverse_link_map[link.canonical_hash] = []
        reverse_link_map[link.canonical_hash].append(link.document_hash)

    books: dict[str, BookSummary] = {}
    for p in all_progress:
        canonical_hash = p.document
        if canonical_hash in books:
            if p.timestamp > books[canonical_hash].timestamp:
                books[canonical_hash] = BookSummary(
                    canonical_hash=canonical_hash,
                    linked_hashes=reverse_link_map.get(canonical_hash, []),
                    label=label_map.get(canonical_hash),
                    filename=p.filename,
                    progress=p.progress,
                    percentage=p.percentage,
                    device=p.device,
                    device_id=p.device_id,
                    timestamp=p.timestamp,
                )
        else:
            books[canonical_hash] = BookSummary(
                canonical_hash=canonical_hash,
                linked_hashes=reverse_link_map.get(canonical_hash, []),
                label=label_map.get(canonical_hash),
                filename=p.filename,
                progress=p.progress,
                percentage=p.percentage,
                device=p.device,
                device_id=p.device_id,
                timestamp=p.timestamp,
            )

    sorted_books = sorted(books.values(), key=lambda b: b.timestamp, reverse=True)
    # Apply pagination
    paginated_books = sorted_books[offset:offset + limit]
    return BooksListResponse(books=paginated_books)


@app.put("/books/label")
def update_book_label(
    request: BookLabelUpdate,
    user: UserEntity = Depends(get_current_user),
    progress_repo=Depends(get_progress_repository),
    label_repo=Depends(get_book_label_repository),
) -> BookLabelResponse:
    """Update or set a book's display label."""
    progress = progress_repo.get_by_user_and_document(user.id, request.canonical_hash)
    if not progress:
        raise HTTPException(status_code=404, detail="Book not found")

    label_entity = label_repo.set_label(user.id, request.canonical_hash, request.label)
    return BookLabelResponse(
        canonical_hash=label_entity.canonical_hash,
        label=label_entity.label,
    )


@app.delete("/books/label/{canonical_hash}")
def delete_book_label(
    canonical_hash: str,
    user: UserEntity = Depends(get_current_user),
    label_repo=Depends(get_book_label_repository),
):
    """Delete a book's custom label (reverts to using filename)."""
    deleted = label_repo.delete_label(user.id, canonical_hash)
    if not deleted:
        raise HTTPException(status_code=404, detail="Label not found")
    return {"status": "success"}


@app.get("/card/{username}")
def get_progress_card(
    username: str,
    limit: int = 5,
    user_repo=Depends(get_user_repository),
    progress_repo=Depends(get_progress_repository),
    link_repo=Depends(get_document_link_repository),
    label_repo=Depends(get_book_label_repository),
):
    """Generate an SVG progress card for embedding in GitHub READMEs."""
    user = user_repo.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    all_progress = progress_repo.get_all_by_user(user.id)
    all_links = link_repo.get_all_links(user.id)
    all_labels = label_repo.get_all_labels(user.id)

    label_map = {label.canonical_hash: label.label for label in all_labels}
    reverse_link_map: dict[str, list[str]] = {}
    for link in all_links:
        if link.canonical_hash not in reverse_link_map:
            reverse_link_map[link.canonical_hash] = []
        reverse_link_map[link.canonical_hash].append(link.document_hash)

    books: dict[str, BookSummary] = {}
    for p in all_progress:
        canonical_hash = p.document
        if canonical_hash in books:
            if p.timestamp > books[canonical_hash].timestamp:
                books[canonical_hash] = BookSummary(
                    canonical_hash=canonical_hash,
                    linked_hashes=reverse_link_map.get(canonical_hash, []),
                    label=label_map.get(canonical_hash),
                    filename=p.filename,
                    progress=p.progress,
                    percentage=p.percentage,
                    device=p.device,
                    device_id=p.device_id,
                    timestamp=p.timestamp,
                )
        else:
            books[canonical_hash] = BookSummary(
                canonical_hash=canonical_hash,
                linked_hashes=reverse_link_map.get(canonical_hash, []),
                label=label_map.get(canonical_hash),
                filename=p.filename,
                progress=p.progress,
                percentage=p.percentage,
                device=p.device,
                device_id=p.device_id,
                timestamp=p.timestamp,
            )

    # Sort by progress (highest first), then by timestamp (most recent first)
    sorted_books = sorted(books.values(), key=lambda b: (b.percentage, b.timestamp), reverse=True)[:limit]
    svg_content = render_progress_card(sorted_books)

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={"Cache-Control": "max-age=1800"}
    )
