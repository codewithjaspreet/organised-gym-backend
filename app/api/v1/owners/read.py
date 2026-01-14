from fastapi import APIRouter, status, Query
from sqlmodel import select
from typing import Optional, List
from app.core.permissions import require_admin
from app.db.db import SessionDep
from app.models.user import User, RoleEnum
from app.models.gym import Gym
from app.models.role import Role
from app.schemas.user import UserResponse, MemberListResponse
from app.schemas.gym import GymResponse
from app.schemas.plan import PlanResponse
from app.schemas.membership import MembershipResponse
from app.schemas.announcement import AnnouncementResponse, AnnouncementListResponse
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.schemas.dashboard import DashboardKPIsResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService
from app.services.announcement_service import AnnouncementService
from app.services.notification_service import NotificationService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/read", tags=["owners"])


def get_owner_gym(current_user: User, session: SessionDep) -> Optional[Gym]:
    """Helper function to get the gym owned by the current admin user"""
    stmt = select(Gym).where(Gym.owner_id == current_user.id)
    gym = session.exec(stmt).first()
    return gym


@router.get("/profile", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def get_owner_profile(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get owner profile"""
    user_service = UserService(session=session)
    user_data = user_service.get_user(current_user.id)
    return success_response(data=user_data, message="Owner profile fetched successfully")


@router.get("/members", response_model=APIResponse[MemberListResponse], status_code=status.HTTP_200_OK)
def get_all_members(
    search: Optional[str] = Query(None, description="Search by name or email"),
    status: Optional[str] = Query("all", description="Filter by status: all, active, expired, new_joins, payment_pending"),
    sort_by: Optional[str] = Query("name_asc", description="Sort by: name_asc, name_desc, newest_joiners, plan_expiry_soonest"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get all members for the owner's gym with filtering, sorting, and pagination"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    
    user_service = UserService(session=session)
    members_data = user_service.get_all_members(
        gym_id=gym.id,
        search=search,
        status=status,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )
    return success_response(data=members_data, message="Members fetched successfully")

@router.get("/dashboard", response_model=APIResponse[DashboardKPIsResponse], status_code=status.HTTP_200_OK)
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Fetch key gym metrics (active members, check-ins, etc.)"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    # Get role name from database
    stmt = select(Role).where(Role.id == current_user.role_id)
    role = session.exec(stmt).first()
    if not role:
        return failure_response(
            message="User role not found",
            data=None
        )
    role_enum = RoleEnum(role.name)
    
    dashboard_service = DashboardService(session=session)
    kpis_data = dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=role_enum,
        gym_id=gym.id
    )
    return success_response(data=kpis_data, message="Dashboard KPIs fetched successfully")


@router.get("/gym", response_model=APIResponse[GymResponse], status_code=status.HTTP_200_OK)
def get_owner_gym_info(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get owner's gym information"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    gym_service = GymService(session=session)
    gym_data = gym_service.get_gym(gym.id)
    return success_response(data=gym_data, message="Gym information fetched successfully")


@router.get("/members/{member_id}", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def get_member(
    member_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a member by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    user_service = UserService(session=session)
    member = user_service.get_user(member_id)
    
    if member.gym_id != gym.id or member.role != "MEMBER":
        return failure_response(
            message="Member not found in your gym",
            data=None
        )
    
    return success_response(data=member, message="Member data fetched successfully")


@router.get("/staff/{staff_id}", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def get_staff(
    staff_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a staff member by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    user_service = UserService(session=session)
    staff = user_service.get_user(staff_id)
    
    if staff.gym_id != gym.id or staff.role != "STAFF":
        return failure_response(
            message="Staff not found in your gym",
            data=None
        )
    
    return success_response(data=staff, message="Staff data fetched successfully")


@router.get("/trainers/{trainer_id}", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def get_trainer(
    trainer_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a trainer by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    user_service = UserService(session=session)
    trainer = user_service.get_user(trainer_id)
    
    if trainer.gym_id != gym.id or trainer.role != "TRAINER":
        return failure_response(
            message="Trainer not found in your gym",
            data=None
        )
    
    return success_response(data=trainer, message="Trainer data fetched successfully")


@router.get("/plans/{plan_id}", response_model=APIResponse[PlanResponse], status_code=status.HTTP_200_OK)
def get_plan(
    plan_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a plan by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    plan_service = PlanService(session=session)
    plan = plan_service.get_plan(plan_id)
    
    if plan.gym_id != gym.id:
        return failure_response(
            message="Plan not found in your gym",
            data=None
        )
    
    return success_response(data=plan, message="Plan fetched successfully")


@router.get("/memberships/{membership_id}", response_model=APIResponse[MembershipResponse], status_code=status.HTTP_200_OK)
def get_membership(
    membership_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get a membership by ID"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    membership_service = MembershipService(session=session)
    membership = membership_service.get_membership(membership_id)
    
    if membership.gym_id != gym.id:
        return failure_response(
            message="Membership not found in your gym",
            data=None
        )
    
    return success_response(data=membership, message="Membership fetched successfully")


@router.get("/announcements", response_model=APIResponse[AnnouncementListResponse], status_code=status.HTTP_200_OK)
def get_announcements(
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get all announcements for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    announcement_service = AnnouncementService(session=session)
    announcements = announcement_service.get_announcements_by_gym(gym_id=gym.id)
    announcements_data = AnnouncementListResponse(announcements=announcements)
    return success_response(data=announcements_data, message="Announcements fetched successfully")


@router.get("/notifications", response_model=APIResponse[NotificationListResponse], status_code=status.HTTP_200_OK)
def get_notifications(
    limit: Optional[int] = Query(100, description="Limit number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Get all notifications for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            data=None
        )
    notification_service = NotificationService(session=session)
    notifications_data = notification_service.get_notifications_by_gym(
        gym_id=gym.id,
        limit=limit,
        offset=offset
    )
    return success_response(data=notifications_data, message="Notifications fetched successfully")

