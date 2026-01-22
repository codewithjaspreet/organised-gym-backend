import os
import json
import logging
import requests
from pathlib import Path
from typing import Optional
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from app.core.config import settings

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
            return path
        return BASE_DIR / path
    
    # Default path
    return BASE_DIR / "organised_gym_service_account.json"


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
    logger.info(
        f"[NOTIFICATION DEBUG] Preparing FCM notification - "
        f"Device Token: {device_token[:20]}..., Title: '{title}', Body: '{body[:50]}...', "
        f"Data: {data if data else 'None'}"
    )
    
    access_token = get_fcm_access_token()
    logger.debug(f"[NOTIFICATION DEBUG] FCM access token obtained successfully")
    
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
        logger.error(
            f"[NOTIFICATION DEBUG] FCM API request failed - Status: {getattr(e.response, 'status_code', 'N/A')}, "
            f"Error: {str(e)}, Response: {getattr(e.response, 'text', 'N/A')[:200]}",
            exc_info=True
        )
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


def send_fcm_notification_to_gym_members_by_filter(
    gym_id: str,
    title: str,
    body: str,
    send_to: str,
    data: Optional[dict] = None,
    session = None,
    member_ids: Optional[list[str]] = None
) -> list[dict]:
    """
    Send FCM notification to gym members based on send_to filter.
    
    Args:
        gym_id: Gym ID
        title: Notification title
        body: Notification body/message
        send_to: Filter type - "All", "Pending Fees", "Birthday", "Plan Expiring Today", "Plan Expiring in 3 days", "Specific Members"
        data: Optional additional data payload
        session: Database session (required)
        member_ids: Optional list of member user IDs (required when send_to is "Specific Members")
        
    Returns:
        list[dict]: List of results for each member with user_id included
    """
    if not session:
        raise ValueError("Database session is required")
    
    from sqlmodel import select, and_, or_, func
    from datetime import date, timedelta
    from app.models.user import User
    from app.models.role import Role as RoleModel
    from app.models.membership import Membership
    from app.models.payments import Payment
    
    # Get MEMBER role
    member_role_stmt = select(RoleModel).where(RoleModel.name == "MEMBER")
    member_role = session.exec(member_role_stmt).first()
    
    if not member_role:
        return []
    
    # Base query for active members with device tokens
    base_conditions = [
        User.gym_id == gym_id,
        User.role_id == member_role.id,
        User.device_token.isnot(None),
        User.is_active == True
    ]
    
    # Apply filter based on send_to parameter
    logger.info(f"[NOTIFICATION DEBUG] Applying filter: send_to='{send_to}'")
    
    if send_to == "All":
        # Get all members
        stmt = select(User).where(and_(*base_conditions))
        members = session.exec(stmt).all()
        logger.info(f"[NOTIFICATION DEBUG] Filter 'All' found {len(members)} members")
        
    elif send_to == "Pending Fees":
        # Get users with pending payments
        today = date.today()
        pending_user_ids_subquery = select(func.distinct(Payment.user_id)).where(
            and_(
                Payment.gym_id == gym_id,
                Payment.status == "pending"
            )
        )
        pending_user_ids = [uid for uid in session.exec(pending_user_ids_subquery).all()]
        
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Pending Fees' found {len(pending_user_ids)} user IDs with pending payments")
        
        if not pending_user_ids:
            logger.info(f"[NOTIFICATION DEBUG] No users with pending fees found, returning empty list")
            return []
        
        stmt = select(User).where(
            and_(
                *base_conditions,
                User.id.in_(pending_user_ids)
            )
        )
        members = session.exec(stmt).all()
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Pending Fees' matched {len(members)} members with device tokens")
        
    elif send_to == "Birthday":
        # Get users whose birthday is today
        # Fetch all members and filter by birthday in Python for cross-database compatibility
        today = date.today()
        all_members_stmt = select(User).where(and_(*base_conditions))
        all_members = session.exec(all_members_stmt).all()
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Birthday' checking {len(all_members)} total members")
        members = [
            member for member in all_members
            if member.dob and member.dob.month == today.month and member.dob.day == today.day
        ]
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Birthday' found {len(members)} members with birthday today")
        
    elif send_to == "Plan Expiring Today":
        # Get users whose membership expires today and is still active
        today = date.today()
        expiring_user_ids_subquery = select(Membership.user_id).where(
            and_(
                Membership.gym_id == gym_id,
                Membership.end_date == today,
                Membership.status == "active",
                Membership.end_date >= today  # Still valid today
            )
        )
        expiring_user_ids = [uid for uid in session.exec(expiring_user_ids_subquery).all()]
        
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Plan Expiring Today' found {len(expiring_user_ids)} user IDs")
        
        if not expiring_user_ids:
            logger.info(f"[NOTIFICATION DEBUG] No members with plan expiring today found, returning empty list")
            return []
        
        stmt = select(User).where(
            and_(
                *base_conditions,
                User.id.in_(expiring_user_ids)
            )
        )
        members = session.exec(stmt).all()
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Plan Expiring Today' matched {len(members)} members with device tokens")
        
    elif send_to == "Plan Expiring in 3 days":
        # Get users whose membership expires in 3 days and is still active
        today = date.today()
        three_days_later = today + timedelta(days=3)
        expiring_user_ids_subquery = select(Membership.user_id).where(
            and_(
                Membership.gym_id == gym_id,
                Membership.end_date == three_days_later,
                Membership.status == "active",
                Membership.end_date >= today  # Still valid
            )
        )
        expiring_user_ids = [uid for uid in session.exec(expiring_user_ids_subquery).all()]
        
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Plan Expiring in 3 days' found {len(expiring_user_ids)} user IDs")
        
        if not expiring_user_ids:
            logger.info(f"[NOTIFICATION DEBUG] No members with plan expiring in 3 days found, returning empty list")
            return []
        
        stmt = select(User).where(
            and_(
                *base_conditions,
                User.id.in_(expiring_user_ids)
            )
        )
        members = session.exec(stmt).all()
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Plan Expiring in 3 days' matched {len(members)} members with device tokens")
        
    elif send_to == "Specific Members":
        # Get specific members by their IDs
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Specific Members' requested for {len(member_ids) if member_ids else 0} member IDs")
        
        if not member_ids:
            logger.info(f"[NOTIFICATION DEBUG] No member_ids provided for 'Specific Members' filter, returning empty list")
            return []
        
        # Verify all member_ids belong to the gym
        stmt = select(User).where(
            and_(
                *base_conditions,
                User.id.in_(member_ids)
            )
        )
        members = session.exec(stmt).all()
        logger.info(f"[NOTIFICATION DEBUG] Filter 'Specific Members' matched {len(members)} members with device tokens out of {len(member_ids)} requested")
        
    else:
        # Invalid send_to value, return empty
        logger.warning(f"[NOTIFICATION DEBUG] Invalid send_to value: '{send_to}', returning empty list")
        return []
    
    if not members:
        logger.info(f"[NOTIFICATION DEBUG] No members found after applying filter, returning empty list")
        return []
    
    logger.info(f"[NOTIFICATION DEBUG] Starting to send notifications to {len(members)} members")
    
    # Send notifications and include user_id in results
    results = []
    for idx, member in enumerate(members, 1):
        if member.device_token:
            logger.info(
                f"[NOTIFICATION DEBUG] Sending notification #{idx}/{len(members)} to user_id={member.id}, "
                f"device_token={member.device_token[:20]}..."
            )
            try:
                result = send_fcm_notification(member.device_token, title, body, data)
                logger.info(
                    f"[NOTIFICATION DEBUG] Notification #{idx} SUCCESS for user_id={member.id}. "
                    f"FCM Response: {result}"
                )
                results.append({
                    "user_id": member.id,
                    "device_token": member.device_token,
                    "success": True,
                    "response": result
                })
            except Exception as e:
                logger.error(
                    f"[NOTIFICATION DEBUG] Notification #{idx} FAILED for user_id={member.id}. "
                    f"Error: {str(e)}",
                    exc_info=True
                )
                results.append({
                    "user_id": member.id,
                    "device_token": member.device_token,
                    "success": False,
                    "error": str(e)
                })
        else:
            logger.warning(f"[NOTIFICATION DEBUG] Member {member.id} has no device_token, skipping")
    
    logger.info(f"[NOTIFICATION DEBUG] Completed sending notifications. Total results: {len(results)}")
    return results
