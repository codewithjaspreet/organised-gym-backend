from fastapi import APIRouter, status, HTTPException, Depends, Query
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
from app.services.announcement_service import AnnouncementService
from app.services.notification_service import NotificationService
from app.services.user_service import UserService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/admin", tags=["owner"])


def get_owner_gym(current_user: User, session: SessionDep) -> Gym:
    """Helper function to get the gym owned by the current admin user"""
    stmt = select(Gym).where(Gym.owner_id == current_user.id)
    gym = session.exec(stmt).first()
    if not gym:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No gym found for this owner"
        )
    return gym

@router.get("/dashboard", response_model=DashboardKPIsResponse)
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Fetch key gym metrics (active members, check-ins, etc.)"""
    gym = get_owner_gym(current_user, session)
    dashboard_service = DashboardService(session=session)
    return dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=current_user.role,
        gym_id=gym.id
    )


# Announcements Endpoints
@router.post("/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement: AnnouncementCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create announcement"""
    gym = get_owner_gym(current_user, session)
    
    # Ensure the announcement is for the owner's gym and set user_id
    if announcement.gym_id != gym.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create announcements for your own gym"
        )
    
    # Set the user_id to current user (owner)
    announcement_dict = announcement.model_dump()
    announcement_dict["user_id"] = current_user.id
    announcement_create = AnnouncementCreate(**announcement_dict)
    
    announcement_service = AnnouncementService(session=session)
    return announcement_service.create_announcement(announcement_create)


@router.get("/announcements", response_model=AnnouncementListResponse)
def get_announcements(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get announcements"""
    gym = get_owner_gym(current_user, session)
    announcement_service = AnnouncementService(session=session)
    announcements = announcement_service.get_announcements_by_gym(gym_id=gym.id)
    return AnnouncementListResponse(announcements=announcements)


# Notifications Endpoints
@router.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification: NotificationCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create notification"""
    gym = get_owner_gym(current_user, session)
    
    # Verify the user belongs to the gym
    from app.models.user import User as UserModel
    user_stmt = select(UserModel).where(
        UserModel.id == notification.user_id,
        UserModel.gym_id == gym.id
    )
    user = session.exec(user_stmt).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to your gym"
        )
    
    notification_service = NotificationService(session=session)
    return notification_service.create_notification(notification=notification)


@router.get("/notifications", response_model=NotificationListResponse)
def get_notifications(
    limit: Optional[int] = Query(100, description="Limit number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get notifications"""
    gym = get_owner_gym(current_user, session)
    notification_service = NotificationService(session=session)
    return notification_service.get_notifications_by_gym(
        gym_id=gym.id,
        limit=limit,
        offset=offset
    )


# Member Management
@router.post("/members", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    user: UserCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Add new member to gym"""
    gym = get_owner_gym(current_user, session)
    
    # Set the gym_id for the new member
    user_dict = user.model_dump()
    user_dict["gym_id"] = gym.id
    user_dict["role"] = user.role if user.role else "MEMBER"
    
    user_service = UserService(session=session)
    return user_service.create_user(UserCreate(**user_dict))


# Profile Endpoints
@router.get("/profile", response_model=UserResponse)
def get_owner_profile(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get owner profile"""
    user_service = UserService(session=session)
    return user_service.get_user(current_user.id)


@router.put("/profile", response_model=UserResponse)
def update_owner_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update owner profile"""
    user_service = UserService(session=session)
    return user_service.update_user(current_user.id, user)

