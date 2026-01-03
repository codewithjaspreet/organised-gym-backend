from fastapi import APIRouter, status, Depends
from app.core.permissions import require_any_authenticated, require_og_or_admin, check_gym_ownership
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.gym import GymCreate, GymResponse, GymUpdate
from app.schemas.user import UserCreate, UserResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.gym_service import GymService
from app.services.user_service import UserService
from app.core.exceptions import NotFoundError, UserNameAlreadyExistsError

router = APIRouter(prefix="/gyms", tags=["gyms"])

@router.post("/", response_model=APIResponse[GymResponse], status_code=status.HTTP_201_CREATED)
def create_gym(
    gym: GymCreate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Users can only create gyms for themselves (unless OG)
    if current_user.role != Role.OG and gym.owner_id != current_user.id:
        return failure_response(
            message="You can only create gyms for yourself",
            status_code=status.HTTP_403_FORBIDDEN
        )
    try:
        gym_service = GymService(session=session)
        gym_data = gym_service.create_gym(gym)
        return success_response(data=gym_data, message="Gym created successfully")
    except Exception as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Failed to create gym",
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.get("/{gym_id}", response_model=APIResponse[GymResponse])
def get_gym(
    gym_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    try:
        gym_service = GymService(session=session)
        gym_data = gym_service.get_gym(gym_id)
        return success_response(data=gym_data, message="Gym data fetched successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Gym not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

@router.put("/{gym_id}", response_model=APIResponse[GymResponse])
def update_gym(
    gym_id: str,
    gym: GymUpdate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    check_gym_ownership(gym_id, current_user, session)
    try:
        gym_service = GymService(session=session)
        updated_gym = gym_service.update_gym(gym_id, gym)
        return success_response(data=updated_gym, message="Gym updated successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Gym not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

@router.delete("/{gym_id}", response_model=APIResponse[dict])
def delete_gym(
    gym_id: str,
    session: SessionDep,
    current_user: User = require_og_or_admin
):
    check_gym_ownership(gym_id, current_user, session)
    try:
        gym_service = GymService(session=session)
        gym_service.delete_gym(gym_id)
        return success_response(data=None, message="Gym deleted successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Gym not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

@router.post("/add-owner" , response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def add_owner(
    user: UserCreate,
    session: SessionDep,
    current_user: User = require_og_or_admin
):
    check_gym_ownership(current_user.gym_id, current_user, session)
    try:
        user_service = UserService(session=session)
        owner_data = user_service.create_user(user)
        return success_response(data=owner_data, message="Owner added successfully")
    except UserNameAlreadyExistsError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Username already exists",
            status_code=status.HTTP_400_BAD_REQUEST
        )