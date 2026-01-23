from fastapi import APIRouter, status
from sqlmodel import select, and_
from datetime import date, timedelta
from app.core.permissions import require_og
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.user import User
from app.models.role import Role as RoleModel
from app.models.og_plan import OGPlan, BillingCycle
from app.models.gym_subscription import GymSubscription, SubscriptionStatus
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.gym import GymResponse, GymUpdate
from app.schemas.og_plan import OGPlanResponse, OGPlanUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.og_plan_service import OGPlanService

router = APIRouter(prefix="/update", tags=["platform-admin"])


@router.put("/owners/{owner_id}", response_model=APIResponse[UserResponse])
def update_owner(
    owner_id: str,
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Update an owner"""
    user_service = UserService(session=session)
    owner = user_service.get_user(owner_id)
    
    if owner.role != "ADMIN":
        return failure_response(
            message="Owner not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    updated_owner = user_service.update_user(owner_id, user)
    return success_response(data=updated_owner, message="Owner updated successfully")


def _calculate_subscription_end_date(start_date: date, billing_cycle: BillingCycle) -> date:
    """Calculate subscription end date based on billing cycle"""
    if billing_cycle == BillingCycle.MONTHLY:
        return start_date + timedelta(days=30)
    elif billing_cycle == BillingCycle.QUARTERLY:
        return start_date + timedelta(days=90)
    elif billing_cycle == BillingCycle.YEARLY:
        return start_date + timedelta(days=365)
    elif billing_cycle == BillingCycle.LIFETIME:
        # Set to 100 years in the future
        return start_date + timedelta(days=36500)
    else:
        return start_date + timedelta(days=30)  # Default to monthly


def _create_or_update_gym_subscription(
    gym_id: str,
    og_plan_id: str,
    session: SessionDep
) -> None:
    """Create or update a gym subscription for the given gym and OG plan"""
    # Verify OG Plan exists
    og_plan_stmt = select(OGPlan).where(OGPlan.id == og_plan_id)
    og_plan = session.exec(og_plan_stmt).first()
    if not og_plan:
        raise NotFoundError(detail=f"OG Plan with id {og_plan_id} not found")
    
    # Check if there's an existing active subscription
    today = date.today()
    existing_subscription_stmt = select(GymSubscription).where(
        and_(
            GymSubscription.gym_id == gym_id,
            GymSubscription.status == SubscriptionStatus.ACTIVE
        )
    ).order_by(GymSubscription.end_date.desc())
    existing_subscription = session.exec(existing_subscription_stmt).first()
    
    if existing_subscription:
        # Update existing subscription
        existing_subscription.og_plan_id = og_plan_id
        existing_subscription.start_date = today
        existing_subscription.end_date = _calculate_subscription_end_date(today, og_plan.billing_cycle)
        existing_subscription.status = SubscriptionStatus.ACTIVE
        session.commit()
    else:
        # Create new subscription
        end_date = _calculate_subscription_end_date(today, og_plan.billing_cycle)
        gym_subscription = GymSubscription(
            gym_id=gym_id,
            og_plan_id=og_plan_id,
            start_date=today,
            end_date=end_date,
            status=SubscriptionStatus.ACTIVE
        )
        session.add(gym_subscription)
        session.commit()


@router.put("/gym", response_model=APIResponse[GymResponse])
def update_gym(
    gym: GymUpdate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Update gym information - accessible by PLATFORM_ADMIN (OG) role. Requires gym_id in request body. Optionally update OG Plan subscription."""
    if not gym.gym_id:
        return failure_response(
            message="gym_id is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    gym_id_to_update = gym.gym_id
    
    # Extract og_plan_id if provided
    og_plan_id = gym.og_plan_id
    
    # Remove gym_id and og_plan_id from update data before passing to service
    update_data = gym.model_dump(exclude_unset=True, exclude={"gym_id", "og_plan_id"})
    gym_update = GymUpdate(**update_data)
    
    gym_service = GymService(session=session)
    updated_gym = gym_service.update_gym(gym_id_to_update, gym_update)
    
    # If og_plan_id is provided, create or update gym subscription
    if og_plan_id:
        try:
            _create_or_update_gym_subscription(gym_id_to_update, og_plan_id, session)
        except NotFoundError as e:
            return failure_response(
                message=str(e.detail) if hasattr(e, 'detail') else str(e),
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    return success_response(data=updated_gym, message="Gym updated successfully")


@router.put("/og-plans/{og_plan_id}", response_model=APIResponse[OGPlanResponse])
def update_og_plan(
    og_plan_id: str,
    og_plan: OGPlanUpdate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Update an OG plan"""
    og_plan_service = OGPlanService(session=session)
    updated_og_plan = og_plan_service.update_og_plan(og_plan_id, og_plan)
    return success_response(data=updated_og_plan, message="OG plan updated successfully")

