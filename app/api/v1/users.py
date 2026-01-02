from fastapi import APIRouter, status, Depends
from app.core.permissions import require_any_authenticated, require_admin, check_ownership_or_admin
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.dashboard import DashboardKPIsResponse
from app.services.user_service import UserService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    user_service = UserService(session=session)
    return user_service.create_user(user)

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


@router.get("/dashboard/kpis", response_model=DashboardKPIsResponse)
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """
    Get dashboard KPIs - response varies by user role.
    
    - ADMIN: Full gym KPIs (active members, check-ins, check-outs, fee due members)
    - MEMBER: Personal stats (own check-ins, check-outs, fee status)
    - STAFF/TRAINER: Limited gym stats (check-ins, check-outs only)
    """
    dashboard_service = DashboardService(session=session)
    return dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=current_user.role,
        gym_id=current_user.gym_id
    )

