from fastapi import APIRouter, HTTPException
from app.core.permissions import require_og
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.response import APIResponse
from app.utils.response import success_response
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
        raise HTTPException(
            status_code=404,
            detail="Owner not found"
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

