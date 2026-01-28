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
from app.utils.email import send_password_reset_email

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


@router.post("/forgot-password", response_model=APIResponse[dict])
def forgot_password(request: ForgotPasswordRequest, session: SessionDep):
    """
    Request password reset. Sends email with reset link if user exists.
    Returns same message regardless of whether user exists to prevent email enumeration.
    """
    # Check if user exists
    stmt = select(User).where(User.email == request.email)
    user = session.exec(stmt).first()
    
    # Always return success message to prevent email enumeration
    # Only send email if user actually exists
    if user:
        # Generate secure token
        token = token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Set expiry to 15 minutes
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        # Create password reset token record
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            used=False
        )
        session.add(reset_token)
        session.commit()
        
        # Generate reset link using configured frontend URL
        frontend_url = config.settings.frontend_url or "https://yourapp.com"
        reset_link = f"{frontend_url}/reset-password?token={token}"
        
        # Send email
        try:
            send_password_reset_email(user.email, reset_link)
        except Exception as e:
            # Log error but don't expose it to user
            print(f"Error sending password reset email: {str(e)}")
            # Still return success to prevent enumeration
    
    return success_response(
        data=None,
        message="If an account with that email exists, a password reset link has been sent."
    )


@router.post("/reset-password", response_model=APIResponse[dict])
def reset_password(request: ResetPasswordRequest, session: SessionDep):
    """
    Reset password using token from email link.
    """
    # Hash the provided token
    token_hash = hashlib.sha256(request.token.encode()).hexdigest()
    
    # Find valid reset token
    stmt = select(PasswordResetToken).where(
        and_(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False
        )
    )
    reset_token = session.exec(stmt).first()
    
    if not reset_token:
        return failure_response(
            message="Invalid or expired reset token",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if token has expired
    if reset_token.expires_at < datetime.utcnow():
        return failure_response(
            message="Reset token has expired. Please request a new password reset.",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Get user
    user_stmt = select(User).where(User.id == reset_token.user_id)
    user = session.exec(user_stmt).first()
    
    if not user:
        return failure_response(
            message="User not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Update password
    user.password_hash = get_password_hash(request.new_password)
    
    # Mark token as used
    reset_token.used = True
    
    # Save changes
    session.add_all([user, reset_token])
    session.commit()
    
    return success_response(
        data=None,
        message="Password has been reset successfully. You can now login with your new password."
    )