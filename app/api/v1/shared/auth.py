from fastapi import APIRouter, Depends, status
from app.db.db import SessionDep
from app.schemas.auth import LoginRequest, LoginResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserCreate, UserResponse
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
    InvalidPasswordError,
    InvalidResetTokenError,
    ResetTokenExpiredError,
    ResetTokenAlreadyUsedError,
    PasswordMismatchError,
    SamePasswordError
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=APIResponse[LoginResponse], status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, session: SessionDep):
    try:
        auth_service = AuthService(session=session)
        user_data = auth_service.register(user)
        return success_response(data=user_data, message="User registered successfully")
    except (UserNameAlreadyExistsError, EmailAlreadyExistsError, PhoneAlreadyExistsError, UserAlreadyExistsError) as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "User is already registered",
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

@router.post("/forgot-password", response_model=APIResponse[None], status_code=status.HTTP_200_OK)
def forgot_password(request: ForgotPasswordRequest, session: SessionDep):
    """
    Request password reset. Sends a reset token to the user's email if the email exists.
    Always returns success to prevent email enumeration attacks.
    """
    try:
        auth_service = AuthService(session=session)
        auth_service.forgot_password(request.email)
        # Always return success message (generic) to prevent email enumeration
        return success_response(
            data=None, 
            message="If an account with that email exists, a password reset link has been sent."
        )
    except Exception as e:
        # Log error but return generic success message for security
        return success_response(
            data=None,
            message="If an account with that email exists, a password reset link has been sent."
        )

@router.post("/reset-password", response_model=APIResponse[None], status_code=status.HTTP_200_OK)
def reset_password(request: ResetPasswordRequest, session: SessionDep):
    """
    Reset password using reset token. Validates token, old password, and enforces password rules.
    """
    try:
        auth_service = AuthService(session=session)
        auth_service.reset_password(
            token=request.token,
            old_password=request.old_password,
            new_password=request.new_password
        )
        return success_response(
            data=None,
            message="Password has been reset successfully"
        )
    except (InvalidResetTokenError, ResetTokenExpiredError, ResetTokenAlreadyUsedError) as e:
        return failure_response(
            message="Invalid or expired reset token",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except PasswordMismatchError as e:
        return failure_response(
            message="Current password is incorrect",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except SamePasswordError as e:
        return failure_response(
            message="New password must be different from the current password",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except ValueError as e:
        return failure_response(
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return failure_response(
            message="An error occurred while resetting your password",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )