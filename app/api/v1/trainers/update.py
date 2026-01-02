from fastapi import APIRouter, HTTPException
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/update", tags=["trainers"])


@router.put("/profile", response_model=UserResponse)
def update_trainer_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Update trainer profile"""
    if current_user.role != Role.TRAINER:
        raise HTTPException(
            status_code=403,
            detail="Only trainers can access this endpoint"
        )
    
    user_service = UserService(session=session)
    return user_service.update_user(current_user.id, user)

