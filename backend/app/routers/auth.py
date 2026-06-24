from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import verify_password, create_access_token, hash_password, require_admin
from app.models.user import User

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "staff"


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(user.username, user.role)
    return LoginResponse(access_token=token, role=user.role)


@router.get("/users", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/users", response_model=UserOut, status_code=201, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()