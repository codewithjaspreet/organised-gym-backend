import os
import json
import requests
from pathlib import Path
from typing import Optional
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from app.core.config import settings


# Path to service account file - use from config or default
BASE_DIR = Path(__file__).resolve().parent.parent
def get_service_account_path() -> Path:
    """Get service account path from config or use default"""
    # Check both firebase_credentials_path and firebase_service_account_path
    service_account_path = (
        settings.firebase_credentials_path or 
        settings.firebase_service_account_path
    )
    
    if service_account_path:
        # If path is absolute, use it directly; otherwise relative to BASE_DIR
        path = Path(service_account_path)
        if path.is_absolute():
            return path
        return BASE_DIR / path
    
    # Default path
    return BASE_DIR / "firebase" / "organised_gym_service_account.json"


def get_fcm_send_url() -> str:
    """Get FCM send URL using project ID from config"""
    return f"https://fcm.googleapis.com/v1/projects/{settings.firebase_project_id}/messages:send"


def get_fcm_access_token() -> str:
    """
    Generate FCM access token using service account credentials.
    
    Returns:
        str: Access token for FCM API
        
    Raises:
        FileNotFoundError: If service account file is not found
        Exception: If token generation fails
    """
    service_account_path = get_service_account_path()
    if not service_account_path.exists():
        raise FileNotFoundError(
            f"Firebase service account file not found at: {service_account_path}"
        )
    
    credentials = service_account.Credentials.from_service_account_file(
        str(service_account_path),
        scopes=["https://www.googleapis.com/auth/firebase.messaging"]
    )
    credentials.refresh(Request())
    return credentials.token


def send_fcm_notification(
    device_token: str,
    title: str,
    body: str,
    data: Optional[dict] = None
) -> dict:
    """
    Send FCM notification to a single device.
    
    Args:
        device_token: FCM device token of the recipient
        title: Notification title
        body: Notification body/message
        data: Optional additional data payload (key-value pairs)
        
    Returns:
        dict: Response from FCM API
        
    Raises:
        Exception: If notification sending fails
    """
    access_token = get_fcm_access_token()
    
    payload = {
        "message": {
            "token": device_token,
            "notification": {
                "title": title,
                "body": body
            }
        }
    }
    
    # Add data payload if provided
    if data:
        payload["message"]["data"] = {str(k): str(v) for k, v in data.items()}
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    fcm_url = get_fcm_send_url()
    response = requests.post(
        fcm_url,
        headers=headers,
        json=payload
    )
    
    # Raise exception if request failed
    response.raise_for_status()
    
    return response.json()


def send_fcm_notification_to_multiple(
    device_tokens: list[str],
    title: str,
    body: str,
    data: Optional[dict] = None
) -> list[dict]:
    """
    Send FCM notification to multiple devices.
    
    Args:
        device_tokens: List of FCM device tokens
        title: Notification title
        body: Notification body/message
        data: Optional additional data payload
        
    Returns:
        list[dict]: List of responses from FCM API for each device
    """
    results = []
    for device_token in device_tokens:
        try:
            result = send_fcm_notification(device_token, title, body, data)
            results.append({"device_token": device_token, "success": True, "response": result})
        except Exception as e:
            results.append({
                "device_token": device_token,
                "success": False,
                "error": str(e)
            })
    
    return results


def send_fcm_notification_to_user(
    user_id: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
    session = None
) -> dict:
    """
    Send FCM notification to a user by user_id.
    Fetches device_token from user record.
    
    Args:
        user_id: User ID to send notification to
        title: Notification title
        body: Notification body/message
        data: Optional additional data payload
        session: Database session (required)
        
    Returns:
        dict: Response from FCM API or error message
        
    Raises:
        ValueError: If session is not provided
        NotFoundError: If user not found or has no device token
    """
    if not session:
        raise ValueError("Database session is required")
    
    from sqlmodel import select
    from app.models.user import User
    from app.core.exceptions import NotFoundError
    
    stmt = select(User).where(User.id == user_id)
    user = session.exec(stmt).first()
    
    if not user:
        raise NotFoundError(detail=f"User with id {user_id} not found")
    
    if not user.device_token:
        raise NotFoundError(detail=f"User {user_id} has no device token registered")
    
    return send_fcm_notification(user.device_token, title, body, data)


def send_fcm_notification_to_gym_members(
    gym_id: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
    session = None
) -> list[dict]:
    """
    Send FCM notification to all members of a gym.
    
    Args:
        gym_id: Gym ID
        title: Notification title
        body: Notification body/message
        data: Optional additional data payload
        session: Database session (required)
        
    Returns:
        list[dict]: List of results for each member
    """
    if not session:
        raise ValueError("Database session is required")
    
    from sqlmodel import select
    from app.models.user import User
    from app.models.role import Role as RoleModel
    
    # Get MEMBER role
    member_role_stmt = select(RoleModel).where(RoleModel.name == "MEMBER")
    member_role = session.exec(member_role_stmt).first()
    
    if not member_role:
        return []
    
    # Get all members of the gym with device tokens
    stmt = select(User).where(
        User.gym_id == gym_id,
        User.role_id == member_role.id,
        User.device_token.isnot(None),
        User.is_active == True
    )
    members = session.exec(stmt).all()
    
    device_tokens = [member.device_token for member in members if member.device_token]
    
    if not device_tokens:
        return []
    
    return send_fcm_notification_to_multiple(device_tokens, title, body, data)
