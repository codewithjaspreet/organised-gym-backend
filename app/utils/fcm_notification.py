import os
import json
import logging
import requests
from pathlib import Path
from typing import Optional
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from app.models.role import Role
from app.core.config import settings
from app.models.membership import Membership
from app.models.payments import Payment
from app.models.user import User
from app.schemas.announcement import SendToType
from typing import Optional
from datetime import date, timedelta
from sqlmodel import select, and_, func
import base64
import json
# Setup logger
logger = logging.getLogger(__name__)


# Path to service account file - use from config or default
BASE_DIR = Path(__file__).resolve().parent.parent.parent
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
            # If absolute path exists, use it
            if path.exists():
                return path

            # Try alternative locations if absolute path doesn't exist
            # This handles the case where env var is set for Docker (/app/...) but running locally
            alternative_paths = []

            # If path starts with /app/, try local equivalents
            if str(path).startswith("/app/"):
                # Remove /app/ prefix and try with BASE_DIR
                relative_path = Path(*path.parts[2:])  # Skip "/" and "app"
                alternative_paths.append(BASE_DIR / relative_path)
                alternative_paths.append(BASE_DIR / "app" / relative_path)
                # Also try /app/app/... for Docker structure
                alternative_paths.append(Path("/app") / "app" / relative_path)

            # Try all alternatives
            for alt_path in alternative_paths:
                if alt_path.exists():
                    return alt_path

            # Return original path (will raise error if not found)
            return path
        return BASE_DIR / service_account_path

    # Default path - try multiple locations
    default_paths = [
        BASE_DIR / "app" / "firebase" / "organised_gym_service_account.json",
        BASE_DIR / "firebase" / "organised_gym_service_account.json",
        Path("/app") / "app" / "firebase" / "organised_gym_service_account.json",
        Path("/app") / "firebase" / "organised_gym_service_account.json",
    ]

    for path in default_paths:
        if path.exists():
            return path

    # Return the first default path if none exist (will raise error later)
    return default_paths[0]


def get_fcm_send_url() -> str:
    """Get FCM send URL using project ID from config"""
    return f"https://fcm.googleapis.com/v1/projects/{settings.firebase_project_id}/messages:send"


def get_fcm_access_token() -> str:
    if not settings.firebase_base_64:
        raise RuntimeError("Firebase base64 credentials not configured")

    # Decode base64 → JSON string
    decoded_json = base64.b64decode(settings.firebase_base_64).decode("utf-8")
    info = json.loads(decoded_json)

    logger.debug(f"loaded info is {info}")

    credentials = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"]
    )

    credentials.refresh(Request())

    logger.debug(
        f"[NOTIFICATION DEBUG] FCM access token obtained, expires at {credentials.expiry}"
    )

    return credentials.token

# def get_fcm_access_token() -> str:
#     # Try FIREBASE_CREDENTIALS first (JSON string), then fallback to base64
#     if settings.firebase_credentials:
#         info = json.loads(settings.firebase_credentials)
#     else:
#         raise RuntimeError("Firebase credentials not configured")

#     credentials = service_account.Credentials.from_service_account_info(
#         info,
#         scopes=["https://www.googleapis.com/auth/firebase.messaging"]
#     )
#     credentials.refresh(Request())
#     logger.debug(f"[NOTIFICATION DEBUG] FCM access token {credentials.token} obtained, expires at {credentials.expiry}")
#     return credentials.token


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
        ValueError: If device_token is empty or invalid
        Exception: If notification sending fails
    """
    # Validate device token
    if not device_token or not device_token.strip():
        raise ValueError("Device token cannot be empty")

    logger.info(
        f"[NOTIFICATION DEBUG] Preparing FCM notification - "
        f"Device Token: {device_token[:20]}..., Title: '{title}', Body: '{body[:50]}...', "
        f"Data: {data if data else 'None'}"
    )

    try:
        access_token = get_fcm_access_token()
        if not access_token:
            raise ValueError("FCM access token is empty")
        logger.debug(f"[NOTIFICATION DEBUG] FCM access token obtained successfully (length: {len(access_token)})")
    except Exception as e:
        logger.error(f"[NOTIFICATION DEBUG] Failed to get FCM access token: {str(e)}")
        raise

    payload = {
        "message": {
            "token": device_token,
            "notification": {
                "title": title,
                "body": body
            },
            "android": {
                "priority": "high"
            },
            "apns": {
                "payload": {
                    "aps": {
                        "sound": "default",
                        "content-available": 1
                    }
                }
            }
        },

    }

    # Add data payload if provided
    if data:
        payload["message"]["data"] = {str(k): str(v) for k, v in data.items()}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    fcm_url = get_fcm_send_url()
    logger.info(f"[NOTIFICATION DEBUG] Sending FCM request to: {fcm_url}")
    logger.debug(f"[NOTIFICATION DEBUG] FCM payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            fcm_url,
            headers=headers,
            json=payload
        )

        logger.info(
            f"[NOTIFICATION DEBUG] FCM API response status: {response.status_code}, "
            f"Response: {response.text[:200]}"
        )

        # Raise exception if request failed
        response.raise_for_status()

        response_json = response.json()
        logger.info(f"[NOTIFICATION DEBUG] FCM notification sent successfully. Response: {response_json}")
        return response_json
    except requests.exceptions.RequestException as e:
        # Log error but don't include full traceback to reduce noise
        error_msg = f"FCM API request failed - Status: {getattr(e.response, 'status_code', 'N/A')}, Error: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            error_msg += f", Response: {e.response.text[:200]}"
        logger.warning(f"[NOTIFICATION DEBUG] {error_msg}")
        raise


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

    # Get MEMBER role
    member_role_stmt = select(Role).where(Role.name == "MEMBER")
    member_role = session.exec(member_role_stmt).first()

    if not member_role:
        return []

    # Get all members of the gym with device tokens
    stmt = select(User).where(
        User.gym_id == gym_id,
        User.role_id == member_role.id,
        User.device_token.isnot(None),
        User.device_token != '',
        User.is_active == True
    )
    members = session.exec(stmt).all()

    device_tokens = [member.device_token for member in members if member.device_token and member.device_token.strip()]

    if not device_tokens:
        return []

    return send_fcm_notification_to_multiple(device_tokens, title, body, data)

def send_fcm_notification_to_gym_members_by_filter(
    gym_id: str,
    title: str,
    body: str,
    send_to: SendToType,
    data: Optional[dict] = None,
    session=None,
    member_ids: Optional[list[str]] = None
) -> list[dict]:
    if not session:
        raise ValueError("Database session is required")

    # Get MEMBER role
    member_role = session.exec(
        select(Role).where(Role.name == "MEMBER")
    ).first()

    if not member_role:
        return []

    base_conditions = [
        User.gym_id == gym_id,
        User.role_id == member_role.id,
        User.device_token.isnot(None),
        User.device_token != '',
        User.is_active == True
    ]

    members: list[User] = []

    if send_to == SendToType.ALL:
        members = session.exec(
            select(User).where(and_(*base_conditions))
        ).all()

    elif send_to == SendToType.PENDING_FEES:
        pending_user_ids = session.exec(
            select(func.distinct(Payment.user_id)).where(
                and_(
                    Payment.gym_id == gym_id,
                    Payment.status == "pending"
                )
            )
        ).all()

        if pending_user_ids:
            members = session.exec(
                select(User).where(
                    and_(*base_conditions, User.id.in_(pending_user_ids))
                )
            ).all()

    elif send_to == SendToType.BIRTHDAY:
        today = date.today()
        all_members = session.exec(
            select(User).where(and_(*base_conditions))
        ).all()

        members = [
            m for m in all_members
            if m.dob and m.dob.month == today.month and m.dob.day == today.day
        ]

    elif send_to == SendToType.PLAN_EXPIRING_TODAY:
        today = date.today()
        expiring_user_ids = session.exec(
            select(Membership.user_id).where(
                and_(
                    Membership.gym_id == gym_id,
                    Membership.end_date == today,
                    Membership.status == "active"
                )
            )
        ).all()

        if expiring_user_ids:
            members = session.exec(
                select(User).where(
                    and_(*base_conditions, User.id.in_(expiring_user_ids))
                )
            ).all()

    elif send_to == SendToType.PLAN_EXPIRING_IN_3_DAYS:
        target_date = date.today() + timedelta(days=3)
        expiring_user_ids = session.exec(
            select(Membership.user_id).where(
                and_(
                    Membership.gym_id == gym_id,
                    Membership.end_date == target_date,
                    Membership.status == "active"
                )
            )
        ).all()

        if expiring_user_ids:
            members = session.exec(
                select(User).where(
                    and_(*base_conditions, User.id.in_(expiring_user_ids))
                )
            ).all()

    elif send_to == SendToType.SPECIFIC_MEMBERS:
        if member_ids:
            members = session.exec(
                select(User).where(
                    and_(*base_conditions, User.id.in_(member_ids))
                )
            ).all()

    if not members:
        return []

    results: list[dict] = []

    for member in members:
        # Skip if device_token is empty or invalid
        if not member.device_token or member.device_token.strip() == '':
            logger.warning(
                f"[NOTIFICATION DEBUG] Skipping user {member.id} - empty or invalid device_token"
            )
            results.append({
                "user_id": member.id,
                "device_token": member.device_token,
                "success": False,
                "error": "Empty or invalid device token"
            })
            continue

        try:
            response = send_fcm_notification(
                member.device_token,
                title,
                body,
                data
            )
            results.append({
                "user_id": member.id,
                "device_token": member.device_token,
                "success": True,
                "response": response
            })
        except Exception as e:
            logger.warning(
                f"[NOTIFICATION DEBUG] Failed to send notification to user {member.id}: {str(e)}"
            )
            results.append({
                "user_id": member.id,
                "device_token": member.device_token,
                "success": False,
                "error": str(e)
            })

    return results


def send_fcm_notification_to_platform_audience(
    send_to: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
    session=None,
    gym_id: Optional[str] = None,
    member_ids: Optional[list[str]] = None,
) -> list[dict]:
    """
    Send FCM notification to platform-level audience: All Users, Owners, Members,
    Specific Gym (all members of that gym), or Specific Member(s).
    """
    if not session:
        raise ValueError("Database session is required")

    from app.schemas.announcement import SendToType

    base_conditions = [
        User.device_token.isnot(None),
        User.device_token != "",
        User.is_active == True,
    ]
    members: list[User] = []

    if send_to == SendToType.ALL_USERS.value:
        stmt = select(User).where(and_(*base_conditions))
        members = list(session.exec(stmt).all())

    elif send_to == SendToType.OWNERS.value:
        admin_role = session.exec(select(Role).where(Role.name == "ADMIN")).first()
        if admin_role:
            stmt = select(User).where(
                and_(*base_conditions, User.role_id == admin_role.id)
            )
            members = list(session.exec(stmt).all())

    elif send_to == SendToType.MEMBERS.value:
        member_role = session.exec(select(Role).where(Role.name == "MEMBER")).first()
        if member_role:
            stmt = select(User).where(
                and_(*base_conditions, User.role_id == member_role.id)
            )
            members = list(session.exec(stmt).all())

    elif send_to == SendToType.SPECIFIC_GYM.value and gym_id:
        member_role = session.exec(select(Role).where(Role.name == "MEMBER")).first()
        if member_role:
            stmt = select(User).where(
                and_(
                    *base_conditions,
                    User.gym_id == gym_id,
                    User.role_id == member_role.id,
                )
            )
            members = list(session.exec(stmt).all())

    elif send_to == SendToType.SPECIFIC_MEMBER.value and member_ids:
        stmt = select(User).where(
            and_(*base_conditions, User.id.in_(member_ids))
        )
        members = list(session.exec(stmt).all())

    if not members:
        return []

    results_platform: list[dict] = []
    for member in members:
        if not member.device_token or member.device_token.strip() == "":
            results_platform.append({
                "user_id": member.id,
                "success": False,
                "error": "Empty or invalid device token",
            })
            continue
        try:
            response = send_fcm_notification(
                member.device_token, title, body, data
            )
            results_platform.append({"user_id": member.id, "success": True, "response": response})
        except Exception as e:
            logger.warning(
                f"[NOTIFICATION DEBUG] Failed to send to user {member.id}: {str(e)}"
            )
            results_platform.append({"user_id": member.id, "success": False, "error": str(e)})
    return results_platform
