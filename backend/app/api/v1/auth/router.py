"""Auth router with mock authentication for development."""

import uuid
from datetime import datetime, UTC

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class AuthUser(BaseModel):
    id: str
    name: str
    email: str
    avatar: str | None = None
    role: str = "user"
    created_at: str


class AuthResponse(BaseModel):
    user: AuthUser
    accessToken: str
    refreshToken: str


def _make_token() -> str:
    return f"tok_{uuid.uuid4().hex}"


@router.post("/login")
async def login(request: LoginRequest):
    user = AuthUser(
        id=str(uuid.uuid4()),
        name=request.email.split("@")[0].title(),
        email=request.email,
        role="admin",
        created_at=datetime.now(UTC).isoformat(),
    )
    return {
        "status": "success",
        "data": {
            "user": user.model_dump(),
            "accessToken": _make_token(),
            "refreshToken": _make_token(),
        },
    }


@router.post("/register")
async def register(request: RegisterRequest):
    user = AuthUser(
        id=str(uuid.uuid4()),
        name=request.name,
        email=request.email,
        role="user",
        created_at=datetime.now(UTC).isoformat(),
    )
    return {
        "status": "success",
        "data": {
            "user": user.model_dump(),
            "accessToken": _make_token(),
            "refreshToken": _make_token(),
        },
    }


@router.post("/refresh")
async def refresh_token():
    return {
        "status": "success",
        "data": {
            "accessToken": _make_token(),
            "refreshToken": _make_token(),
        },
    }


@router.post("/logout")
async def logout():
    return {"status": "success", "message": "Logged out successfully"}
