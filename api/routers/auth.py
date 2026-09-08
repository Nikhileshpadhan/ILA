"""Signup, login, and current-user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import authenticate, create_access_token, get_current_user, hash_password
from ..database import get_db
from ..db_models import DBUser
from ..schemas import AuthRequest, AuthResponse, SignupRequest, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _user_response(user: DBUser) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name)


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.lower().strip()
    if db.scalar(select(DBUser).where(DBUser.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = DBUser(email=email, display_name=payload.display_name.strip(), password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthResponse(access_token=create_access_token(user.id), user=_user_response(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = authenticate(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return AuthResponse(access_token=create_access_token(user.id), user=_user_response(user))


@router.get("/me", response_model=UserResponse)
def me(user: DBUser = Depends(get_current_user)) -> UserResponse:
    return _user_response(user)