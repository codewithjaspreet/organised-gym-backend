from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permissions import require_admin
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.schemas.user import UserCreate, UserResponse
from app.schemas.member import AddMemberRequest
from app.schemas.gym import GymCreate, GymResponse
from app.schemas.plan import PlanCreate, PlanResponse
from app.schemas.membership import MembershipCreate, MembershipResponse
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse
from app.schemas.gym_rule import GymRuleCreate, GymRuleResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService
from app.services.announcement_service import AnnouncementService

router = APIRouter(prefix="/create", tags=["owners"])


def get_owner_gym(current_user: User, session: SessionDep):
    """Helper function to get the gym owned by the current admin user"""
    stmt = select(Gym).where(Gym.owner_id == current_user.id)
    return session.exec(stmt).first()


@router.post("/members", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def add_member(
    request: AddMemberRequest,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Add an existing member to the owner's gym by username"""
    # Validate that the gym exists and belongs to this owner
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if request.gym_id != gym.id:
        return failure_response(
            message="You can only add members to your own gym",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    user_service = UserService(session=session)
    member_data = user_service.add_member_to_gym(
        member_user_name=request.member_user_name,
        gym_id=request.gym_id,
        plan_id=request.plan_id,
        new_duration=request.new_duration,
        new_price=request.new_price
    )
    return success_response(data=member_data, message="Member added to gym successfully")


@router.post("/staff", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def create_staff(
    user: UserCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new staff member for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    user_dict = user.model_dump()
    user_dict["gym_id"] = gym.id
    user_dict["role"] = "STAFF"
    
    user_service = UserService(session=session)
    staff_data = user_service.create_user(UserCreate(**user_dict))
    return success_response(data=staff_data, message="Staff created successfully")


@router.post("/trainers", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def create_trainer(
    user: UserCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new trainer for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    user_dict = user.model_dump()
    user_dict["gym_id"] = gym.id
    user_dict["role"] = "TRAINER"
    
    user_service = UserService(session=session)
    trainer_data = user_service.create_user(UserCreate(**user_dict))
    return success_response(data=trainer_data, message="Trainer created successfully")


@router.post("/plans", response_model=APIResponse[PlanResponse], status_code=status.HTTP_201_CREATED)
def create_plan(
    plan: PlanCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new plan for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if plan.gym_id != gym.id:
        return failure_response(
            message="You can only create plans for your own gym",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    plan_service = PlanService(session=session)
    plan_data = plan_service.create_plan(plan)
    return success_response(data=plan_data, message="Plan created successfully")


@router.post("/memberships", response_model=APIResponse[MembershipResponse], status_code=status.HTTP_201_CREATED)
def create_membership(
    membership: MembershipCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new membership for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if membership.gym_id != gym.id:
        return failure_response(
            message="You can only create memberships for your own gym",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    membership_service = MembershipService(session=session)
    membership_data = membership_service.create_membership(membership)
    return success_response(data=membership_data, message="Membership created successfully")


@router.post("/announcements", response_model=APIResponse[AnnouncementResponse], status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement: AnnouncementCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new announcement for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if announcement.gym_id != gym.id:
        return failure_response(
            message="You can only create announcements for your own gym",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    announcement_dict = announcement.model_dump()
    announcement_dict["user_id"] = current_user.id
    announcement_create = AnnouncementCreate(**announcement_dict)
    
    announcement_service = AnnouncementService(session=session)
    announcement_data = announcement_service.create_announcement(announcement_create)
    return success_response(data=announcement_data, message="Announcement created successfully")




@router.post("/rules", response_model=APIResponse[GymRuleResponse], status_code=status.HTTP_201_CREATED)
def create_gym_rule(
    rule: GymRuleCreate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Create a new gym rule for the owner's gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if rule.gym_id != gym.id:
        return failure_response(
            message="You can only create rules for your own gym",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    gym_service = GymService(session=session)
    rule_data = gym_service.create_gym_rule(rule)
    return success_response(data=rule_data, message="Gym rule created successfully")

