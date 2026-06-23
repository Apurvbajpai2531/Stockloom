from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.auth import ADMIN_USERNAME, verify_password, create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    if payload.username != ADMIN_USERNAME or not verify_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token(payload.username)
    return LoginResponse(access_token=token)
