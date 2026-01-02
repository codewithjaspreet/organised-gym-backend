from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select
from typing import Optional, List
from app.core.permissions import require_admin
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.schemas.user import UserResponse
from app.schemas.gym import GymResponse
from app.schemas.plan import PlanResponse
from app.schemas.membership import MembershipResponse
from app.schemas.announcement import AnnouncementResponse, AnnouncementListResponse
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.schemas.dashboard import DashboardKPIsResponse
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService
from app.services.announcement_service import AnnouncementService
from app.services.notification_service import NotificationService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/read", tags=["owners"])


def get_owner_gym(current_user: User, session: SessionDep) -> Gym:
    """Helper function to get the gym owned by the current admin user"""
    stmt = select(Gym).where(Gym.owner_id == current_user.id)
    gym = session.exec(stmt).first()
    if not gym:
        raise HTTPException(
            status_code=404,
            detail="No gym found for this owner"
        )
    return gym


@router.get("/profile", response_model=UserResponse)
def get_owner_profile(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get owner profile"""
    user_service = UserService(session=session)
    return user_service.get_user(current_user.id)


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


@router.get("/gym", response_model=GymResponse)
def get_owner_gym_info(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get owner's gym information"""
    gym = get_owner_gym(current_user, session)
    gym_service = GymService(session=session)
    return gym_service.get_gym(gym.id)


@router.get("/members/{member_id}", response_model=UserResponse)
def get_member(
    member_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a member by ID"""
    gym = get_owner_gym(current_user, session)
    user_service = UserService(session=session)
    member = user_service.get_user(member_id)
    
    if member.gym_id != gym.id or member.role != "MEMBER":
        raise HTTPException(
            status_code=404,
            detail="Member not found in your gym"
        )
    
    return member


@router.get("/staff/{staff_id}", response_model=UserResponse)
def get_staff(
    staff_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a staff member by ID"""
    gym = get_owner_gym(current_user, session)
    user_service = UserService(session=session)
    staff = user_service.get_user(staff_id)
    
    if staff.gym_id != gym.id or staff.role != "STAFF":
        raise HTTPException(
            status_code=404,
            detail="Staff not found in your gym"
        )
    
    return staff


@router.get("/trainers/{trainer_id}", response_model=UserResponse)
def get_trainer(
    trainer_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a trainer by ID"""
    gym = get_owner_gym(current_user, session)
    user_service = UserService(session=session)
    trainer = user_service.get_user(trainer_id)
    
    if trainer.gym_id != gym.id or trainer.role != "TRAINER":
        raise HTTPException(
            status_code=404,
            detail="Trainer not found in your gym"
        )
    
    return trainer


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a plan by ID"""
    gym = get_owner_gym(current_user, session)
    plan_service = PlanService(session=session)
    plan = plan_service.get_plan(plan_id)
    
    if plan.gym_id != gym.id:
        raise HTTPException(
            status_code=404,
            detail="Plan not found in your gym"
        )
    
    return plan


@router.get("/memberships/{membership_id}", response_model=MembershipResponse)
def get_membership(
    membership_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a membership by ID"""
    gym = get_owner_gym(current_user, session)
    membership_service = MembershipService(session=session)
    membership = membership_service.get_membership(membership_id)
    
    if membership.gym_id != gym.id:
        raise HTTPException(
            status_code=404,
            detail="Membership not found in your gym"
        )
    
    return membership


@router.get("/announcements", response_model=AnnouncementListResponse)
def get_announcements(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get all announcements for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    announcement_service = AnnouncementService(session=session)
    announcements = announcement_service.get_announcements_by_gym(gym_id=gym.id)
    return AnnouncementListResponse(announcements=announcements)


@router.get("/notifications", response_model=NotificationListResponse)
def get_notifications(
    limit: Optional[int] = Query(100, description="Limit number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get all notifications for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    notification_service = NotificationService(session=session)
    return notification_service.get_notifications_by_gym(
        gym_id=gym.id,
        limit=limit,
        offset=offset
    )

