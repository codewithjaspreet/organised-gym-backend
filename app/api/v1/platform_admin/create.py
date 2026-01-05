from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permission_guard import require_permission
from app.db.db import SessionDep
from app.models.user import User
from app.models.gym import Gym
from app.models.role import Role
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
    user_service = UserService(session=session)
    owner_data = user_service.create_user(UserCreate(**user_dict))
    return success_response(data=owner_data, message="Owner created successfully")


@router.post("/gyms", response_model=APIResponse[GymResponse], status_code=status.HTTP_201_CREATED)
def create_gym(
    gym: GymCreate,
    session: SessionDep = None,
    current_user: User = require_permission("gym_create")
):
    """Create a new gym. Requires gym_create permission. Requires owner_id of an ADMIN user."""
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
    
    gym_service = GymService(session=session)
    gym_data = gym_service.create_gym(gym)
    return success_response(data=gym_data, message="Gym created successfully")


@router.post("/og-plans", response_model=APIResponse[OGPlanResponse], status_code=status.HTTP_201_CREATED)
def create_og_plan(
    og_plan: OGPlanCreate,
    session: SessionDep = None,
    current_user: User = require_permission("og_plan_create")
):
    """Create a new OG plan. Requires og_plan_create permission."""
    og_plan_service = OGPlanService(session=session)
    og_plan_data = og_plan_service.create_og_plan(og_plan)
    return success_response(data=og_plan_data, message="OG plan created successfully")

