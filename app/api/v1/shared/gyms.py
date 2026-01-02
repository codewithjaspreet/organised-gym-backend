from fastapi import APIRouter, status, Depends, HTTPException
from app.core.permissions import require_any_authenticated, require_og_or_admin, check_gym_ownership
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.gym import GymCreate, GymResponse, GymUpdate
from app.schemas.user import UserCreate, UserResponse
from app.services.gym_service import GymService
from app.services.user_service import UserService

router = APIRouter(prefix="/gyms", tags=["gyms"])

@router.post("/", response_model=GymResponse, status_code=status.HTTP_201_CREATED)
def create_gym(
    gym: GymCreate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Users can only create gyms for themselves (unless OG)
    if current_user.role != Role.OG and gym.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create gyms for yourself"
        )
    gym_service = GymService(session=session)
    return gym_service.create_gym(gym)

@router.get("/{gym_id}", response_model=GymResponse)
def get_gym(
    gym_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    gym_service = GymService(session=session)
    return gym_service.get_gym(gym_id)

@router.put("/{gym_id}", response_model=GymResponse)
def update_gym(
    gym_id: str,
    gym: GymUpdate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    check_gym_ownership(gym_id, current_user, session)
    gym_service = GymService(session=session)
    return gym_service.update_gym(gym_id, gym)

@router.delete("/{gym_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gym(
    gym_id: str,
    session: SessionDep,
    current_user: User = require_og_or_admin
):
    check_gym_ownership(gym_id, current_user, session)
    gym_service = GymService(session=session)
    return gym_service.delete_gym(gym_id)

@router.post("/add-owner" , response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def add_owner(
    user: UserCreate,
    session: SessionDep,
    current_user: User = require_og_or_admin
):
    check_gym_ownership(current_user.gym_id, current_user, session)
    user_service = UserService(session=session)
    return user_service.create_user(user)