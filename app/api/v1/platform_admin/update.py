from fastapi import APIRouter, HTTPException
from app.core.permissions import require_og
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.gym import GymResponse, GymUpdate
from app.schemas.og_plan import OGPlanResponse, OGPlanUpdate
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.og_plan_service import OGPlanService

router = APIRouter(prefix="/update", tags=["platform-admin"])


@router.put("/owners/{owner_id}", response_model=UserResponse)
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
        raise HTTPException(
            status_code=404,
            detail="Owner not found"
        )
    
    return user_service.update_user(owner_id, user)


@router.put("/gyms/{gym_id}", response_model=GymResponse)
def update_gym(
    gym_id: str,
    gym: GymUpdate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Update a gym"""
    gym_service = GymService(session=session)
    return gym_service.update_gym(gym_id, gym)


@router.put("/og-plans/{og_plan_id}", response_model=OGPlanResponse)
def update_og_plan(
    og_plan_id: str,
    og_plan: OGPlanUpdate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Update an OG plan"""
    og_plan_service = OGPlanService(session=session)
    return og_plan_service.update_og_plan(og_plan_id, og_plan)

