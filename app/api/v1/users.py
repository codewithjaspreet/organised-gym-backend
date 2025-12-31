from fastapi import APIRouter, status, Depends
from app.core.permissions import require_any_authenticated, require_admin, check_ownership_or_admin
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    check_ownership_or_admin(user_id, current_user)
    user_service = UserService(session=session)
    return user_service.get_user(user_id)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user: UserUpdate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    check_ownership_or_admin(user_id, current_user)
    user_service = UserService(session=session)
    return user_service.update_user(user_id, user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    session: SessionDep,
    current_user: User = require_admin
):
    user_service = UserService(session=session)
    return user_service.delete_user(user_id)

