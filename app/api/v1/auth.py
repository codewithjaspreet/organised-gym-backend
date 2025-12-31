from fastapi import APIRouter, Depends, status
from app.db.db import SessionDep
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, session: SessionDep):
    auth_service = AuthService(session=session)
    return auth_service.register(user)

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, session: SessionDep):
    auth_service = AuthService(session=session)
    return auth_service.login(credentials)