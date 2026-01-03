from fastapi import APIRouter, status, Depends, Query
from sqlmodel import select
from typing import Optional, List
from datetime import date
from app.core.permissions import require_admin
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
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
    current_user: User = require_admin
):
    """Fetch key gym metrics (active members, check-ins, etc.)"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    dashboard_service = DashboardService(session=session)
    kpis_data = dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=current_user.role,
        gym_id=gym.id
    )
    return success_response(data=kpis_data, message="Dashboard KPIs fetched successfully")


# Announcements Endpoints
@router.post("/announcements", response_model=APIResponse[AnnouncementResponse], status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement: AnnouncementCreate,
    session: SessionDep = None,
    current_user: User = require_admin
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
    current_user: User = require_admin
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
    current_user: User = require_admin
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
    current_user: User = require_admin
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
    current_user: User = require_admin
):
    """Add new member to gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Set the gym_id for the new member
    user_dict = user.model_dump()
    user_dict["gym_id"] = gym.id
    user_dict["role"] = user.role if user.role else "MEMBER"
    
    user_service = UserService(session=session)
    member_data = user_service.create_user(UserCreate(**user_dict))
    return success_response(data=member_data, message="Member added successfully")


# Profile Endpoints
@router.get("/profile", response_model=APIResponse[UserResponse])
def get_owner_profile(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get owner profile"""
    user_service = UserService(session=session)
    user_data = user_service.get_user(current_user.id)
    return success_response(data=user_data, message="Owner profile fetched successfully")


@router.put("/profile", response_model=APIResponse[UserResponse])
def update_owner_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update owner profile"""
    user_service = UserService(session=session)
    updated_user = user_service.update_user(current_user.id, user)
    return success_response(data=updated_user, message="Owner profile updated successfully")

