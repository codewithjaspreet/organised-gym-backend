from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import select, and_
from secrets import token_urlsafe
from datetime import datetime, timedelta
import hashlib
from app.db.db import SessionDep
from app.schemas.auth import LoginRequest, LoginResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserCreate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.auth_service import AuthService
from app.core.exceptions import (
    UserNameAlreadyExistsError,
    EmailAlreadyExistsError,
    PhoneAlreadyExistsError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidPhoneError,
    InvalidUserNameError,
    InvalidPasswordError
)
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.core.security import get_password_hash
from app.core import config

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=APIResponse[LoginResponse], status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, session: SessionDep):
    try:
        auth_service = AuthService(session=session)
        login_data = auth_service.register(user)
        return success_response(data=login_data, message="User registered and logged in successfully")
    except (UserNameAlreadyExistsError, EmailAlreadyExistsError, PhoneAlreadyExistsError, UserAlreadyExistsError) as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "User already exists",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except (InvalidEmailError, InvalidPhoneError, InvalidUserNameError, InvalidPasswordError) as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Invalid input",
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.post("/login", response_model=APIResponse[LoginResponse])
def login(credentials: LoginRequest, session: SessionDep):
    try:
        auth_service = AuthService(session=session)
        login_data = auth_service.login(credentials)
        return success_response(data=login_data, message="Login successful")
    except InvalidCredentialsError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Invalid credentials",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

