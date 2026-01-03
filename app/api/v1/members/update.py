from fastapi import APIRouter, HTTPException
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response
from app.services.user_service import UserService

router = APIRouter(prefix="/update", tags=["members"])


@router.put("/profile", response_model=APIResponse[UserResponse])
def update_member_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Update member profile"""
    if current_user.role != Role.MEMBER:
        raise HTTPException(
            status_code=403,
            detail="Only members can access this endpoint"
        )
    
    user_service = UserService(session=session)
    updated_user = user_service.update_user(current_user.id, user)
    return success_response(data=updated_user, message="Member profile updated successfully")

