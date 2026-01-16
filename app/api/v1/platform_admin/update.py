from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permissions import require_og
from app.db.db import SessionDep
from app.models.user import User
from app.models.role import Role as RoleModel
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


@router.put("/gym", response_model=APIResponse[GymResponse])
def update_gym(
    gym: GymUpdate,
    session: SessionDep = None,
    current_user: User = require_og
):
    """Update gym information - accessible by PLATFORM_ADMIN (OG) role. Requires gym_id in request body."""
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

