from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User
from app.models.role import Role as RoleModel
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService

router = APIRouter(prefix="/update", tags=["members"])


def _is_member(current_user: User, session: SessionDep) -> bool:
    if not current_user.role_id:
        return False
    role = session.exec(select(RoleModel).where(RoleModel.id == current_user.role_id)).first()
    return role is not None and role.name == "MEMBER"


@router.put("/profile", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def update_member_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Update member profile"""
    if not _is_member(current_user, session):
        return failure_response(
            message="Only members can access this endpoint",
            data=None
        )
    user_service = UserService(session=session)
    updated_user = user_service.update_user(current_user.id, user)
    return success_response(data=updated_user, message="Member profile updated successfully")


@router.post("/leave-gym", response_model=APIResponse[dict], status_code=status.HTTP_200_OK)
def leave_gym(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Leave the current gym. Deactivates the member from the gym and cancels/deactivates any active plan linked to the gym."""
    if not _is_member(current_user, session):
        return failure_response(
            message="Only members can access this endpoint",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )
    from app.core.exceptions import NotFoundError, UserNotFoundError
    try:
        user_service = UserService(session=session)
        user_service.leave_gym(user_id=current_user.id)
        return success_response(data={}, message="You have left the gym successfully")
    except (NotFoundError, UserNotFoundError) as e:
        return failure_response(
            message=getattr(e, "detail", str(e)),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )

