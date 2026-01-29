from fastapi import APIRouter, status
from sqlmodel import select, and_
from datetime import date
from app.core.permissions import require_admin
from app.db.db import SessionDep
from app.models.role import Role
from app.models.user import User
from app.models.gym import Gym
from app.models.membership import Membership
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService

router = APIRouter(prefix="/delete", tags=["owners"])


def get_owner_gym(current_user: User, session: SessionDep):
    """Helper function to get the gym owned by the current admin user"""
    stmt = select(Gym).where(Gym.owner_id == current_user.id)
    return session.exec(stmt).first()


@router.delete("/members/{member_id}", response_model=APIResponse[dict])
def delete_member(
    member_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Delete a member"""
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
    
    user_service.delete_user(member_id)
    return success_response(data=None, message="Member deleted successfully")


@router.delete("/members/{member_id}/deactivate", response_model=APIResponse[dict])
def deactivate_member_plan_and_remove_from_gym(
    member_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Deactivate member's plan and remove member from gym"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    user_service = UserService(session=session)
    member = user_service.get_user(member_id)

    role_stmt = select(Role).where(Role.name == "MEMBER")
    role = session.exec(role_stmt).first()  
    if member.gym_id != gym.id or member.role_id != role.id:
        return failure_response(
            message="Member not found in your gym",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Deactivate all active memberships for this member
    today = date.today()
    active_memberships_stmt = select(Membership).where(
        and_(
            Membership.user_id == member_id,
            Membership.gym_id == gym.id,
            Membership.status == "active"
        )
    )
    active_memberships = session.exec(active_memberships_stmt).all()
    
    for membership in active_memberships:
        membership.status = "expired"
        if membership.end_date > today:
            membership.end_date = today
    
    # Remove member from gym (set gym_id and plan_id to None)
    member.gym_id = None
    member.plan_id = None
    
    session.commit()
    
    return success_response(data=None, message="Member plan deactivated and removed from gym successfully")


@router.delete("/staff/{staff_id}", response_model=APIResponse[dict])
def delete_staff(
    staff_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Delete a staff member"""
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
    
    membership_service.delete_membership(membership_id)
    return success_response(data=None, message="Membership deleted successfully")


@router.delete("/rules/{rule_id}", response_model=APIResponse[dict])
def delete_gym_rule(
    rule_id: str,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Delete a gym rule"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    gym_service = GymService(session=session)
    existing_rule = gym_service.get_gym_rule(rule_id)
    
    if existing_rule.gym_id != gym.id:
        return failure_response(
            message="Rule not found in your gym",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    gym_service.delete_gym_rule(rule_id)
    return success_response(data=None, message="Gym rule deleted successfully")

