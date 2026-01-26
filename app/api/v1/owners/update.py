from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permissions import require_admin, require_og_or_admin
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.models.role import Role as RoleModel
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.gym import GymResponse, GymUpdate
from app.schemas.plan import PlanResponse, PlanUpdate
from app.schemas.membership import MembershipResponse, MembershipUpdate
from app.schemas.gym_rule import GymRuleResponse, GymRuleUpdate
from app.schemas.payments import PaymentResponse, PaymentStatusUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService
from app.services.membership_service import MembershipService
from app.services.payment import PaymentService
from app.models.payments import Payment
from app.core.exceptions import NotFoundError

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
def update_gym(
    gym: GymUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update gym information - accessible by ADMIN role. Requires gym_id in request body."""
    if not gym.gym_id:
        return failure_response(
            message="gym_id is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    gym_id_to_update = gym.gym_id
    
    # Remove gym_id from update data before passing to service
    update_data = gym.model_dump(exclude_unset=True, exclude={"gym_id"})
    gym_update = GymUpdate(**update_data)
    
    gym_service = GymService(session=session)
    updated_gym = gym_service.update_gym(gym_id_to_update, gym_update)
    return success_response(data=updated_gym, message="Gym updated successfully")


@router.put("/members/{member_id}", response_model=APIResponse[UserResponse])
def update_member(
    member_id: str,
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a member. Set gym_id to null to remove member from gym."""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    user_service = UserService(session=session)
    member = user_service.get_user(member_id)
    
    # Check if member belongs to owner's gym
    if member.gym_id != gym.id or member.role != "MEMBER":
        return failure_response(
            message="Member not found in your gym",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Allow gym_id=null to remove member from gym
    # If gym_id is being set, validate it's either null or the owner's gym
    update_data = user.model_dump(exclude_unset=True)
    if 'gym_id' in update_data:
        new_gym_id = update_data['gym_id']
        if new_gym_id is not None and new_gym_id != gym.id:
            return failure_response(
                message="You can only assign members to your own gym or remove them (gym_id=null)",
                status_code=status.HTTP_403_FORBIDDEN
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


@router.put("/rules/{rule_id}", response_model=APIResponse[GymRuleResponse])
def update_gym_rule(
    rule_id: str,
    rule: GymRuleUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Update a gym rule"""
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
    
    updated_rule = gym_service.update_gym_rule(rule_id, rule)
    return success_response(data=updated_rule, message="Gym rule updated successfully")


@router.put("/payments/status", response_model=APIResponse[PaymentResponse], status_code=status.HTTP_200_OK)
def update_payment_status(
    payment_status_update: PaymentStatusUpdate,
    session: SessionDep = None,
    current_user: User = require_admin
):
    """Approve or reject a payment and send notification to member"""
    gym = get_owner_gym(current_user, session)
    if not gym:
        return failure_response(
            message="No gym found for this owner",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Verify payment belongs to owner's gym
    stmt = select(Payment).where(Payment.id == payment_status_update.payment_id)
    payment = session.exec(stmt).first()
    
    if not payment:
        return failure_response(
            message="Payment not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if payment.gym_id != gym.id:
        return failure_response(
            message="Payment does not belong to your gym",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check if payment is already in the requested state
    if payment_status_update.status.value == "Approve" and payment.status == "verified":
        return failure_response(
            message="Payment is already approved",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    if payment_status_update.status.value == "Reject" and payment.status == "rejected":
        return failure_response(
            message="Payment is already rejected",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    payment_service = PaymentService(session=session)
    try:
        updated_payment = payment_service.update_payment_status(
            payment_status_update=payment_status_update,
            verified_by=current_user.id
        )
        
        status_message = "approved" if payment_status_update.status.value == "Approve" else "rejected"
        return success_response(
            data=updated_payment, 
            message=f"Payment {status_message} successfully"
        )
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return failure_response(
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )

