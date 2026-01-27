from fastapi import APIRouter, status
from sqlmodel import select, and_
from app.core.permissions import require_og
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym_subscription import GymSubscription, SubscriptionStatus
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.og_plan_service import OGPlanService

router = APIRouter(prefix="/delete", tags=["platform-admin"])


@router.delete("/owners/{owner_id}", response_model=APIResponse[dict])
def delete_owner(
    owner_id: str,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Delete an owner"""
    user_service = UserService(session=session)
    owner = user_service.get_user(owner_id)
    
    if owner.role != "ADMIN":
        return failure_response(
            message="Owner not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    user_service.delete_user(owner_id)
    return success_response(data=None, message="Owner deleted successfully")


@router.delete("/gyms/{gym_id}", response_model=APIResponse[dict])
def delete_gym(
    gym_id: str,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Delete a gym"""
    gym_service = GymService(session=session)
    gym_service.delete_gym(gym_id)
    return success_response(data=None, message="Gym deleted successfully")


@router.delete("/gyms/{gym_id}/og-plan", response_model=APIResponse[dict])
def deactivate_gym_og_plan(
    gym_id: str,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Deactivate a gym's OG plan subscription"""
    # Verify gym exists
    gym_service = GymService(session=session)
    try:
        gym = gym_service.get_gym(gym_id)
    except NotFoundError:
        return failure_response(
            message="Gym not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Find active subscription for this gym
    subscription_stmt = select(GymSubscription).where(
        and_(
            GymSubscription.gym_id == gym_id,
            GymSubscription.status == SubscriptionStatus.ACTIVE
        )
    ).order_by(GymSubscription.end_date.desc())
    active_subscription = session.exec(subscription_stmt).first()
    
    if not active_subscription:
        return failure_response(
            message="No active OG plan subscription found for this gym",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Deactivate the subscription
    active_subscription.status = SubscriptionStatus.CANCELLED
    session.commit()
    
    return success_response(data=None, message="Gym OG plan subscription deactivated successfully")


@router.delete("/og-plans/{og_plan_id}", response_model=APIResponse[dict])
def delete_og_plan(
    og_plan_id: str,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Delete an OG plan"""
    og_plan_service = OGPlanService(session=session)
    og_plan_service.delete_og_plan(og_plan_id)
    return success_response(data=None, message="OG plan deleted successfully")

