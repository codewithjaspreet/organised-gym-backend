from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.core.permissions import require_admin
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.gym import GymResponse, GymUpdate
from app.schemas.plan import PlanResponse, PlanUpdate
from app.schemas.membership import MembershipResponse, MembershipUpdate
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService

router = APIRouter(prefix="/update", tags=["owners"])


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


@router.put("/profile", response_model=UserResponse)
def update_owner_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update owner profile"""
    user_service = UserService(session=session)
    return user_service.update_user(current_user.id, user)


@router.put("/gym", response_model=GymResponse)
def update_owner_gym(
    gym: GymUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update owner's gym information"""
    owner_gym = get_owner_gym(current_user, session)
    gym_service = GymService(session=session)
    return gym_service.update_gym(owner_gym.id, gym)


@router.put("/members/{member_id}", response_model=UserResponse)
def update_member(
    member_id: str,
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a member"""
    gym = get_owner_gym(current_user, session)
    user_service = UserService(session=session)
    member = user_service.get_user(member_id)
    
    if member.gym_id != gym.id or member.role != "MEMBER":
        raise HTTPException(
            status_code=404,
            detail="Member not found in your gym"
        )
    
    return user_service.update_user(member_id, user)


@router.put("/staff/{staff_id}", response_model=UserResponse)
def update_staff(
    staff_id: str,
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a staff member"""
    gym = get_owner_gym(current_user, session)
    user_service = UserService(session=session)
    staff = user_service.get_user(staff_id)
    
    if staff.gym_id != gym.id or staff.role != "STAFF":
        raise HTTPException(
            status_code=404,
            detail="Staff not found in your gym"
        )
    
    return user_service.update_user(staff_id, user)


@router.put("/trainers/{trainer_id}", response_model=UserResponse)
def update_trainer(
    trainer_id: str,
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a trainer"""
    gym = get_owner_gym(current_user, session)
    user_service = UserService(session=session)
    trainer = user_service.get_user(trainer_id)
    
    if trainer.gym_id != gym.id or trainer.role != "TRAINER":
        raise HTTPException(
            status_code=404,
            detail="Trainer not found in your gym"
        )
    
    return user_service.update_user(trainer_id, user)


@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: str,
    plan: PlanUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a plan"""
    gym = get_owner_gym(current_user, session)
    plan_service = PlanService(session=session)
    existing_plan = plan_service.get_plan(plan_id)
    
    if existing_plan.gym_id != gym.id:
        raise HTTPException(
            status_code=404,
            detail="Plan not found in your gym"
        )
    
    return plan_service.update_plan(plan_id, plan)


@router.put("/memberships/{membership_id}", response_model=MembershipResponse)
def update_membership(
    membership_id: str,
    membership: MembershipUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a membership"""
    gym = get_owner_gym(current_user, session)
    membership_service = MembershipService(session=session)
    existing_membership = membership_service.get_membership(membership_id)
    
    if existing_membership.gym_id != gym.id:
        raise HTTPException(
            status_code=404,
            detail="Membership not found in your gym"
        )
    
    return membership_service.update_membership(membership_id, membership)

