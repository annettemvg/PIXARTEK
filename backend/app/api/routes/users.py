"""PIXARTEK — Autenticación local (username + password)."""
import hashlib
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.user import User

log = logging.getLogger("users")
router = APIRouter(prefix="/users", tags=["users"])


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    name: str
    email: str
    picture: str
    level: str


@router.post("/register", response_model=UserResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if username taken
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El nombre de usuario ya existe")

    user = User(
        username=body.username,
        password_hash=_hash(body.password),
        name=body.name,
        email="",
        picture="",
        level="principiante",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    log.info("New user registered: %s", body.username)
    return UserResponse(id=str(user.id), username=user.username, name=user.name, email=user.email or "", picture=user.picture, level=user.level)


@router.post("/login", response_model=UserResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or user.password_hash != _hash(body.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return UserResponse(id=str(user.id), username=user.username, name=user.name, email=user.email or "", picture=user.picture, level=user.level)
