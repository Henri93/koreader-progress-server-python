import os
import hashlib
import bcrypt
from fastapi import Header, HTTPException, Depends

from repositories import get_user_repository
from repositories.protocols import UserEntity

_salt = os.getenv("PASSWORD_SALT")
if not _salt:
    raise RuntimeError(
        "PASSWORD_SALT environment variable is required. "
        "Generate one with: openssl rand -hex 32"
    )
PASSWORD_SALT = _salt.encode()


def md5_hash(password: str) -> str:
    """Convert raw password to MD5 hash."""
    return hashlib.md5(password.encode()).hexdigest()


def hash_password(password_md5: str) -> str:
    """Hash an MD5 password for storage using bcrypt."""
    salted = PASSWORD_SALT + password_md5.encode()
    # bcrypt has a max input length of 72 bytes
    return bcrypt.hashpw(salted[:72], bcrypt.gensalt()).decode()


def verify_password(password_md5: str, password_hash: str) -> bool:
    """Verify MD5 password against stored bcrypt hash."""
    salted = PASSWORD_SALT + password_md5.encode()
    # bcrypt has a max input length of 72 bytes
    return bcrypt.checkpw(salted[:72], password_hash.encode())


def get_current_user(
    x_auth_user: str = Header(None),
    x_auth_key: str = Header(None),
    user_repo=Depends(get_user_repository),
) -> UserEntity:
    # Avoid logging credentials or auth failure details (prevents enumeration)
    if not x_auth_user or not x_auth_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = user_repo.get_by_username(x_auth_user)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not verify_password(x_auth_key, user.password_hash):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return user
