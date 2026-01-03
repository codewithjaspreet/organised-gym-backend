from fastapi import APIRouter, status
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response

router = APIRouter(prefix="/delete", tags=["members"])


@router.delete("/profile", response_model=APIResponse[dict], status_code=status.HTTP_200_OK)
def delete_member_profile(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Delete member profile (soft delete - deactivate account)"""
    if current_user.role != Role.MEMBER:
        return failure_response(
            message="Only members can access this endpoint",
            data=None
        )
    
    from app.services.user_service import UserService
    from app.schemas.user import UserUpdate
    
    user_service = UserService(session=session)
    user_update = UserUpdate(is_active=False)
    user_service.update_user(current_user.id, user_update)
    
    return success_response(data=None, message="Member profile deleted successfully")

