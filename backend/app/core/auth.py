import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed: str) -> bool:
    return pwd_context.verify(plain_password, hashed)


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "role": role, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role", "staff")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_admin(role: str = Depends(get_current_user_role)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return role


def ensure_default_admin(db: Session):
    """Creates a default admin user on first run if no users exist."""
    if db.query(User).count() == 0:
        default_user = os.getenv("ADMIN_USERNAME", "admin")
        default_pass = os.getenv("ADMIN_PASSWORD", "stockloom123")
        db.add(User(username=default_user, password_hash=hash_password(default_pass), role="admin"))
        db.commit()