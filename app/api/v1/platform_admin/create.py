from fastapi import APIRouter, status
from sqlmodel import select, and_
from datetime import date, timedelta
from app.core.permission_guard import require_permission
from app.core.permissions import require_og
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.models.role import Role
from app.models.og_plan import OGPlan, BillingCycle
from app.models.gym_subscription import GymSubscription, SubscriptionStatus
from app.schemas.user import UserCreate, UserResponse
from app.schemas.gym import GymCreate, GymResponse
from app.schemas.og_plan import OGPlanCreate, OGPlanResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.og_plan_service import OGPlanService

router = APIRouter(prefix="/create", tags=["platform-admin"])


@router.post("/owners", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def create_owner(
    user: UserCreate,
    session: SessionDep = None,
    current_user: User = require_permission("user_create")
):
    """Create a new gym owner (ADMIN role). Requires user_create permission."""
    user_dict = user.model_dump()
    user_dict["role"] = "ADMIN"  # Override role to ADMIN
    user_service = UserService(session=session)
    owner_data = user_service.create_user(UserCreate(**user_dict))
    return success_response(data=owner_data, message="Owner created successfully")


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


def _create_gym_subscription(
    gym_id: str,
    og_plan_id: str,
    session: SessionDep
) -> None:
    """Create a gym subscription for the given gym and OG plan"""
    # Verify OG Plan exists
    og_plan_stmt = select(OGPlan).where(OGPlan.id == og_plan_id)
    og_plan = session.exec(og_plan_stmt).first()
    if not og_plan:
        raise NotFoundError(detail=f"OG Plan with id {og_plan_id} not found")
    
    # Calculate subscription dates
    today = date.today()
    end_date = _calculate_subscription_end_date(today, og_plan.billing_cycle)
    
    # Create gym subscription
    gym_subscription = GymSubscription(
        gym_id=gym_id,
        og_plan_id=og_plan_id,
        start_date=today,
        end_date=end_date,
        status=SubscriptionStatus.ACTIVE
    )
    session.add(gym_subscription)
    session.commit()


@router.post("/gyms", response_model=APIResponse[GymResponse], status_code=status.HTTP_201_CREATED)
def create_gym(
    gym: GymCreate,
    session: SessionDep = None,
    current_user: User = require_permission("gym_create")
):
    """Create a new gym with OG Plan subscription. Requires gym_create permission. Requires owner_id of an ADMIN user and og_plan_id."""
    # Get ADMIN role
    stmt = select(Role).where(Role.name == "ADMIN")
    admin_role = session.exec(stmt).first()
    if not admin_role:
        return failure_response(
            message="ADMIN role not found in system",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Validate that owner_id exists and is an ADMIN role user
    stmt = select(User).where(User.id == gym.owner_id)
    owner = session.exec(stmt).first()
    if not owner:
        return failure_response(
            message=f"Owner with id {gym.owner_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if owner.role_id != admin_role.id:
        return failure_response(
            message=f"User with id {gym.owner_id} is not an ADMIN. Only ADMIN users can own gyms.",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate og_plan_id is provided (mandatory)
    if not gym.og_plan_id:
        return failure_response(
            message="og_plan_id is required",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify OG Plan exists
    og_plan_stmt = select(OGPlan).where(OGPlan.id == gym.og_plan_id)
    og_plan = session.exec(og_plan_stmt).first()
    if not og_plan:
        return failure_response(
            message=f"OG Plan with id {gym.og_plan_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Create gym (without og_plan_id in the gym data)
    gym_dict = gym.model_dump(exclude={"og_plan_id"})
    gym_create = GymCreate(**gym_dict)
    gym_service = GymService(session=session)
    gym_data = gym_service.create_gym(gym_create)
    
    # Create gym subscription
    try:
        _create_gym_subscription(gym_data.id, gym.og_plan_id, session)
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return success_response(data=gym_data, message="Gym created successfully with OG Plan subscription")


@router.post("/og-plans", response_model=APIResponse[OGPlanResponse], status_code=status.HTTP_201_CREATED)
def create_og_plan(
    og_plan: OGPlanCreate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Create a new OG plan. Requires OG role."""
    og_plan_service = OGPlanService(session=session)
    og_plan_data = og_plan_service.create_og_plan(og_plan)
    return success_response(data=og_plan_data, message="OG plan created successfully")

