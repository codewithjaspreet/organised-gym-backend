from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permissions import require_admin
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.gym import GymResponse, GymUpdate
from app.schemas.plan import PlanResponse, PlanUpdate
from app.schemas.membership import MembershipResponse, MembershipUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService

router = APIRouter(prefix="/update", tags=["owners"])


def get_owner_gym(current_user: User, session: SessionDep):
    """Helper function to get the gym owned by the current admin user"""
    stmt = select(Gym).where(Gym.owner_id == current_user.id)
    return session.exec(stmt).first()


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


@router.put("/gym", response_model=APIResponse[GymResponse])
def update_owner_gym(
    gym: GymUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update owner's gym information"""
    owner_gym = get_owner_gym(current_user, session)
    if not owner_gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    gym_service = GymService(session=session)
    updated_gym = gym_service.update_gym(owner_gym.id, gym)
    return success_response(data=updated_gym, message="Gym updated successfully")


@router.put("/members/{member_id}", response_model=APIResponse[UserResponse])
def update_member(
    member_id: str,
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a member"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    user_service = UserService(session=session)
    member = user_service.get_user(member_id)
    
    if member.gym_id != gym.id or member.role != "MEMBER":
        return failure_response(
            message="Member not found in your gym",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    updated_member = user_service.update_user(member_id, user)
    return success_response(data=updated_member, message="Member updated successfully")


@router.put("/staff/{staff_id}", response_model=APIResponse[UserResponse])
def update_staff(
    staff_id: str,
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a staff member"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    user_service = UserService(session=session)
    staff = user_service.get_user(staff_id)
    
    if staff.gym_id != gym.id or staff.role != "STAFF":
        return failure_response(
            message="Staff not found in your gym",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    updated_staff = user_service.update_user(staff_id, user)
    return success_response(data=updated_staff, message="Staff updated successfully")


@router.put("/trainers/{trainer_id}", response_model=APIResponse[UserResponse])
def update_trainer(
    trainer_id: str,
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a trainer"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    user_service = UserService(session=session)
    trainer = user_service.get_user(trainer_id)
    
    if trainer.gym_id != gym.id or trainer.role != "TRAINER":
        return failure_response(
            message="Trainer not found in your gym",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    updated_trainer = user_service.update_user(trainer_id, user)
    return success_response(data=updated_trainer, message="Trainer updated successfully")


@router.put("/plans/{plan_id}", response_model=APIResponse[PlanResponse])
def update_plan(
    plan_id: str,
    plan: PlanUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a plan"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    plan_service = PlanService(session=session)
    existing_plan = plan_service.get_plan(plan_id)
    
    if existing_plan.gym_id != gym.id:
        return failure_response(
            message="Plan not found in your gym",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    updated_plan = plan_service.update_plan(plan_id, plan)
    return success_response(data=updated_plan, message="Plan updated successfully")


@router.put("/memberships/{membership_id}", response_model=APIResponse[MembershipResponse])
def update_membership(
    membership_id: str,
    membership: MembershipUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a membership"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    membership_service = MembershipService(session=session)
    existing_membership = membership_service.get_membership(membership_id)
    
    if existing_membership.gym_id != gym.id:
        return failure_response(
            message="Membership not found in your gym",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    updated_membership = membership_service.update_membership(membership_id, membership)
    return success_response(data=updated_membership, message="Membership updated successfully")

