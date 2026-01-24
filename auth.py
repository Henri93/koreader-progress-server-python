import os
import logging
import hashlib
import bcrypt
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

PASSWORD_SALT = os.getenv("PASSWORD_SALT", "default-salt-change-me").encode()


def md5_hash(password: str) -> str:
    """Convert raw password to MD5 hash."""
    return hashlib.md5(password.encode()).hexdigest()


def hash_password(password_md5: str) -> str:
    """Hash an MD5 password for storage using bcrypt."""
    salted = PASSWORD_SALT + password_md5.encode()
    return bcrypt.hashpw(salted, bcrypt.gensalt()).decode()


def verify_password(password_md5: str, password_hash: str) -> bool:
    """Verify MD5 password against stored bcrypt hash."""
    salted = PASSWORD_SALT + password_md5.encode()
    return bcrypt.checkpw(salted, password_hash.encode())


def get_current_user(
    x_auth_user: str = Header(None),
    x_auth_key: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    key_hint = f"'{x_auth_key[:8]}...' len={len(x_auth_key)}" if x_auth_key else "None"
    logger.debug(f"Auth: user='{x_auth_user}' key={key_hint}")

    if not x_auth_user or not x_auth_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.username == x_auth_user).first()
    if not user:
        logger.debug(f"User '{x_auth_user}' not found")
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not verify_password(x_auth_key, user.password_hash):
        logger.debug(f"Password mismatch for '{x_auth_user}'")
        raise HTTPException(status_code=401, detail="Unauthorized")

    logger.debug(f"Auth OK for '{x_auth_user}'")
    return user
