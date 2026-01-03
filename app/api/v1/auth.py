from fastapi import APIRouter, Depends, status
from app.db.db import SessionDep
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserCreate, UserResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, session: SessionDep):
    auth_service = AuthService(session=session)
    user_data = auth_service.register(user)
    return success_response(data=user_data, message="User registered successfully")

@router.post("/login", response_model=APIResponse[LoginResponse])
def login(credentials: LoginRequest, session: SessionDep):
    auth_service = AuthService(session=session)
    login_data = auth_service.login(credentials)
    return success_response(data=login_data, message="Login successful")