from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.core.permissions import require_admin
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.schemas.response import APIResponse
from app.utils.response import success_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService

router = APIRouter(prefix="/delete", tags=["owners"])


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


@router.delete("/members/{member_id}", response_model=APIResponse[dict])
def delete_member(
    member_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Delete a member"""
    gym = get_owner_gym(current_user, session)
    user_service = UserService(session=session)
    member = user_service.get_user(member_id)
    
    if member.gym_id != gym.id or member.role != "MEMBER":
        raise HTTPException(
            status_code=404,
            detail="Member not found in your gym"
        )
    
    user_service.delete_user(member_id)
    return success_response(data=None, message="Member deleted successfully")


@router.delete("/staff/{staff_id}", response_model=APIResponse[dict])
def delete_staff(
    staff_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Delete a staff member"""
    gym = get_owner_gym(current_user, session)
    user_service = UserService(session=session)
    staff = user_service.get_user(staff_id)
    
    if staff.gym_id != gym.id or staff.role != "STAFF":
        raise HTTPException(
            status_code=404,
            detail="Staff not found in your gym"
        )
    
    user_service.delete_user(staff_id)
    return success_response(data=None, message="Staff deleted successfully")


@router.delete("/trainers/{trainer_id}", response_model=APIResponse[dict])
def delete_trainer(
    trainer_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Delete a trainer"""
    gym = get_owner_gym(current_user, session)
    user_service = UserService(session=session)
    trainer = user_service.get_user(trainer_id)
    
    if trainer.gym_id != gym.id or trainer.role != "TRAINER":
        raise HTTPException(
            status_code=404,
            detail="Trainer not found in your gym"
        )
    
    user_service.delete_user(trainer_id)
    return success_response(data=None, message="Trainer deleted successfully")


@router.delete("/plans/{plan_id}", response_model=APIResponse[dict])
def delete_plan(
    plan_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Delete a plan"""
    gym = get_owner_gym(current_user, session)
    plan_service = PlanService(session=session)
    existing_plan = plan_service.get_plan(plan_id)
    
    if existing_plan.gym_id != gym.id:
        raise HTTPException(
            status_code=404,
            detail="Plan not found in your gym"
        )
    
    plan_service.delete_plan(plan_id)
    return success_response(data=None, message="Plan deleted successfully")


@router.delete("/memberships/{membership_id}", response_model=APIResponse[dict])
def delete_membership(
    membership_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Delete a membership"""
    gym = get_owner_gym(current_user, session)
    membership_service = MembershipService(session=session)
    existing_membership = membership_service.get_membership(membership_id)
    
    if existing_membership.gym_id != gym.id:
        raise HTTPException(
            status_code=404,
            detail="Membership not found in your gym"
        )
    
    membership_service.delete_membership(membership_id)
    return success_response(data=None, message="Membership deleted successfully")

