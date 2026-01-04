from fastapi import APIRouter, status, Depends, Query
from sqlmodel import select
from typing import Optional, List
from datetime import date
from app.core.permission_guard import require_permission, require_any_permission
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.models.role import Role
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse, AnnouncementListResponse
from app.schemas.notification import NotificationCreate, NotificationResponse, NotificationListResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.dashboard import DashboardKPIsResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.announcement_service import AnnouncementService
from app.services.notification_service import NotificationService
from app.services.user_service import UserService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/admin", tags=["owner"])


def get_owner_gym(current_user: User, session: SessionDep):
    """Helper function to get the gym owned by the current admin user"""
    stmt = select(Gym).where(Gym.owner_id == current_user.id)
    return session.exec(stmt).first()

@router.get("/dashboard", response_model=APIResponse[DashboardKPIsResponse])
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_any_permission("user_get_all", "gym_get_own")
):
    """Fetch key gym metrics (active members, check-ins, etc.)"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    dashboard_service = DashboardService(session=session)
    # Get role name from role_id
    stmt = select(Role).where(Role.id == current_user.role_id)
    role = session.exec(stmt).first()
    role_name = role.name if role else "MEMBER"
    
    kpis_data = dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=role_name,
        gym_id=gym.id
    )
    return success_response(data=kpis_data, message="Dashboard KPIs fetched successfully")


# Announcements Endpoints
@router.post("/announcements", response_model=APIResponse[AnnouncementResponse], status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement: AnnouncementCreate,
    session: SessionDep = None,
    current_user: User = require_permission("gym_get_own")  # Can create announcements if they can access their gym
):
    """Create announcement"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Ensure the announcement is for the owner's gym and set user_id
    if announcement.gym_id != gym.id:
        return failure_response(
            message="You can only create announcements for your own gym",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Set the user_id to current user (owner)
    announcement_dict = announcement.model_dump()
    announcement_dict["user_id"] = current_user.id
    announcement_create = AnnouncementCreate(**announcement_dict)
    
    announcement_service = AnnouncementService(session=session)
    announcement_data = announcement_service.create_announcement(announcement_create)
    return success_response(data=announcement_data, message="Announcement created successfully")


@router.get("/announcements", response_model=APIResponse[AnnouncementListResponse])
def get_announcements(
    session: SessionDep = None,
    current_user: User = require_permission("gym_get_own")
):
    """Get announcements"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    announcement_service = AnnouncementService(session=session)
    announcements = announcement_service.get_announcements_by_gym(gym_id=gym.id)
    announcements_data = AnnouncementListResponse(announcements=announcements)
    return success_response(data=announcements_data, message="Announcements fetched successfully")


# Notifications Endpoints
@router.post("/notifications", response_model=APIResponse[NotificationResponse], status_code=status.HTTP_201_CREATED)
def create_notification(
    notification: NotificationCreate,
    session: SessionDep = None,
    current_user: User = require_permission("user_get_all")  # Can create notifications if they can see users
):
    """Create notification"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Verify the user belongs to the gym
    from app.models.user import User as UserModel
    user_stmt = select(UserModel).where(
        UserModel.id == notification.user_id,
        UserModel.gym_id == gym.id
    )
    user = session.exec(user_stmt).first()
    if not user:
        return failure_response(
            message="User does not belong to your gym",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    notification_service = NotificationService(session=session)
    notification_data = notification_service.create_notification(notification=notification)
    return success_response(data=notification_data, message="Notification created successfully")


@router.get("/notifications", response_model=APIResponse[NotificationListResponse])
def get_notifications(
    limit: Optional[int] = Query(100, description="Limit number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    session: SessionDep = None,
    current_user: User = require_permission("gym_get_own")
):
    """Get notifications"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    notification_service = NotificationService(session=session)
    notifications_data = notification_service.get_notifications_by_gym(
        gym_id=gym.id,
        limit=limit,
        offset=offset
    )
    return success_response(data=notifications_data, message="Notifications fetched successfully")


# Member Management
@router.post("/members", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def add_member(
    user: UserCreate,
    session: SessionDep = None,
    current_user: User = require_permission("user_create")
):
    """Add new member to gym. Requires user_create permission. Owner must pass gym_id explicitly"""
    if not user.gym_id:
        return failure_response(
            message="gym_id is required when creating a member",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate that the gym exists and belongs to this owner
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if user.gym_id != gym.id:
        return failure_response(
            message="You can only create members for your own gym",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Override role to MEMBER
    user_dict = user.model_dump()
    user_dict["role"] = "MEMBER"  # Set role name to MEMBER
    # gym_id is already in user_dict from model_dump
    
    user_service = UserService(session=session)
    member_data = user_service.create_user(UserCreate(**user_dict))
    return success_response(data=member_data, message="Member added successfully")


# Profile Endpoints
@router.get("/profile", response_model=APIResponse[UserResponse])
def get_owner_profile(
    session: SessionDep = None,
    current_user: User = require_any_permission("user_get_all", "user_get_own")
):
    """Get owner profile. Requires user_get_all or user_get_own permission."""
    user_service = UserService(session=session)
    user_data = user_service.get_user(current_user.id)
    return success_response(data=user_data, message="Owner profile fetched successfully")


@router.put("/profile", response_model=APIResponse[UserResponse])
def update_owner_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_permission("user_update")
):
    """Update owner profile"""
    user_service = UserService(session=session)
    updated_user = user_service.update_user(current_user.id, user)
    return success_response(data=updated_user, message="Owner profile updated successfully")

