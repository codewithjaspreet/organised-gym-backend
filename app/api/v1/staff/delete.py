from fastapi import APIRouter, HTTPException
from app.core.permissions import require_admin_or_staff
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.response import APIResponse
from app.utils.response import success_response

router = APIRouter(prefix="/delete", tags=["staff"])


@router.delete("/profile", response_model=APIResponse[dict])
def delete_staff_profile(
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Delete staff profile (soft delete - deactivate account)"""
    if current_user.role != Role.STAFF:
        raise HTTPException(
            status_code=403,
            detail="Only staff can access this endpoint"
        )
    
    from app.services.user_service import UserService
    from app.schemas.user import UserUpdate
    
    user_service = UserService(session=session)
    user_update = UserUpdate(is_active=False)
    user_service.update_user(current_user.id, user_update)
    
    return success_response(data=None, message="Staff profile deleted successfully")

