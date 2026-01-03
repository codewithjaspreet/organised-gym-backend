from fastapi import APIRouter, status
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService

router = APIRouter(prefix="/update", tags=["trainers"])


@router.put("/profile", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def update_trainer_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Update trainer profile"""
    if current_user.role != Role.TRAINER:
        return failure_response(
            message="Only trainers can access this endpoint",
            data=None
        )
    
    user_service = UserService(session=session)
    updated_user = user_service.update_user(current_user.id, user)
    return success_response(data=updated_user, message="Trainer profile updated successfully")

