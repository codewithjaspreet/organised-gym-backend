from fastapi import APIRouter, status
from app.core.permissions import require_og
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.gym import GymCreate, GymResponse
from app.schemas.og_plan import OGPlanCreate, OGPlanResponse
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.og_plan_service import OGPlanService

router = APIRouter(prefix="/create", tags=["platform-admin"])


@router.post("/owners", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_owner(
    user: UserCreate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Create a new gym owner (ADMIN role)"""
    user_dict = user.model_dump()
    user_dict["role"] = "ADMIN"
    
    user_service = UserService(session=session)
    return user_service.create_user(UserCreate(**user_dict))


@router.post("/gyms", response_model=GymResponse, status_code=status.HTTP_201_CREATED)
def create_gym(
    gym: GymCreate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Create a new gym (platform admin can create for any owner)"""
    gym_service = GymService(session=session)
    return gym_service.create_gym(gym)


@router.post("/og-plans", response_model=OGPlanResponse, status_code=status.HTTP_201_CREATED)
def create_og_plan(
    og_plan: OGPlanCreate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Create a new OG plan"""
    og_plan_service = OGPlanService(session=session)
    return og_plan_service.create_og_plan(og_plan)

