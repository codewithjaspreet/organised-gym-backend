from fastapi import APIRouter, status, HTTPException
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role

router = APIRouter(prefix="/delete", tags=["members"])


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
def delete_member_profile(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Delete member profile (soft delete - deactivate account)"""
    if current_user.role != Role.MEMBER:
        raise HTTPException(
            status_code=403,
            detail="Only members can access this endpoint"
        )
    
    from app.services.user_service import UserService
    from app.schemas.user import UserUpdate
    
    user_service = UserService(session=session)
    user_update = UserUpdate(is_active=False)
    user_service.update_user(current_user.id, user_update)
    
    return None

