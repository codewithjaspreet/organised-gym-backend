from fastapi import APIRouter, HTTPException
from app.core.permissions import require_og
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.user import UserResponse
from app.schemas.gym import GymResponse
from app.schemas.og_plan import OGPlanResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response
from app.services.user_service import UserService
from app.services.gym_service import GymService
from app.services.og_plan_service import OGPlanService

router = APIRouter(prefix="/read", tags=["platform-admin"])


@router.get("/owners/{owner_id}", response_model=APIResponse[UserResponse])
def get_owner(
    owner_id: str,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Get an owner by ID"""
    user_service = UserService(session=session)
    owner = user_service.get_user(owner_id)
    
    if owner.role != "ADMIN":
        raise HTTPException(
            status_code=404,
            detail="Owner not found"
        )
    
    return success_response(data=owner, message="Owner data fetched successfully")


@router.get("/gyms/{gym_id}", response_model=APIResponse[GymResponse])
def get_gym(
    gym_id: str,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Get a gym by ID"""
    gym_service = GymService(session=session)
    gym_data = gym_service.get_gym(gym_id)
    return success_response(data=gym_data, message="Gym data fetched successfully")


@router.get("/og-plans/{og_plan_id}", response_model=APIResponse[OGPlanResponse])
def get_og_plan(
    og_plan_id: str,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Get an OG plan by ID"""
    og_plan_service = OGPlanService(session=session)
    og_plan_data = og_plan_service.get_og_plan(og_plan_id)
    return success_response(data=og_plan_data, message="OG plan fetched successfully")

