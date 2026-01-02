from fastapi import APIRouter, status, HTTPException
from sqlmodel import select
from app.core.permissions import require_admin
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.schemas.user import UserCreate, UserResponse
from app.schemas.gym import GymCreate, GymResponse
from app.schemas.plan import PlanCreate, PlanResponse
from app.schemas.membership import MembershipCreate, MembershipResponse
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService
from app.services.announcement_service import AnnouncementService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/create", tags=["owners"])


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


@router.post("/members", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_member(
    user: UserCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new member for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    
    user_dict = user.model_dump()
    user_dict["gym_id"] = gym.id
    user_dict["role"] = "MEMBER"
    
    user_service = UserService(session=session)
    return user_service.create_user(UserCreate(**user_dict))


@router.post("/staff", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    user: UserCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new staff member for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    
    user_dict = user.model_dump()
    user_dict["gym_id"] = gym.id
    user_dict["role"] = "STAFF"
    
    user_service = UserService(session=session)
    return user_service.create_user(UserCreate(**user_dict))


@router.post("/trainers", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_trainer(
    user: UserCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new trainer for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    
    user_dict = user.model_dump()
    user_dict["gym_id"] = gym.id
    user_dict["role"] = "TRAINER"
    
    user_service = UserService(session=session)
    return user_service.create_user(UserCreate(**user_dict))


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    plan: PlanCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new plan for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    
    if plan.gym_id != gym.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create plans for your own gym"
        )
    
    plan_service = PlanService(session=session)
    return plan_service.create_plan(plan)


@router.post("/memberships", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
def create_membership(
    membership: MembershipCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new membership for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    
    if membership.gym_id != gym.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create memberships for your own gym"
        )
    
    membership_service = MembershipService(session=session)
    return membership_service.create_membership(membership)


@router.post("/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement: AnnouncementCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new announcement for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    
    if announcement.gym_id != gym.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create announcements for your own gym"
        )
    
    announcement_dict = announcement.model_dump()
    announcement_dict["user_id"] = current_user.id
    announcement_create = AnnouncementCreate(**announcement_dict)
    
    announcement_service = AnnouncementService(session=session)
    return announcement_service.create_announcement(announcement_create)


@router.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(
    notification: NotificationCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new notification for a user in the owner's gym"""
    gym = get_owner_gym(current_user, session)
    
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

