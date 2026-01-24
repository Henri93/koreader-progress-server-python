import os
import bcrypt
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User

PASSWORD_SALT = os.getenv("PASSWORD_SALT", "default-salt-change-me").encode()


def hash_password(password: str) -> str:
    salted = PASSWORD_SALT + password.encode()
    return bcrypt.hashpw(salted, bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    salted = PASSWORD_SALT + password.encode()
    return bcrypt.checkpw(salted, password_hash.encode())


def get_current_user(
    x_auth_user: str = Header(None),
    x_auth_key: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    if not x_auth_user or not x_auth_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter(User.username == x_auth_user).first()
    if not user or not verify_password(x_auth_key, user.password_hash):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return user
