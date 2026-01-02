from fastapi import APIRouter, HTTPException
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.user import UserResponse
from app.schemas.dashboard import DashboardKPIsResponse
from app.services.user_service import UserService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/read", tags=["trainers"])


@router.get("/profile", response_model=UserResponse)
def get_trainer_profile(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get trainer profile"""
    if current_user.role != Role.TRAINER:
        raise HTTPException(
            status_code=403,
            detail="Only trainers can access this endpoint"
        )
    
    user_service = UserService(session=session)
    return user_service.get_user(current_user.id)


@router.get("/dashboard", response_model=DashboardKPIsResponse)
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get trainer dashboard KPIs"""
    if current_user.role != Role.TRAINER:
        raise HTTPException(
            status_code=403,
            detail="Only trainers can access this endpoint"
        )
    
    dashboard_service = DashboardService(session=session)
    return dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=current_user.role,
        gym_id=current_user.gym_id
    )

