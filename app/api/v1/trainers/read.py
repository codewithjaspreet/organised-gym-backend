from fastapi import APIRouter, status
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.user import UserResponse
from app.schemas.dashboard import DashboardKPIsResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/read", tags=["trainers"])


@router.get("/profile", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def get_trainer_profile(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get trainer profile"""
    if current_user.role != Role.TRAINER:
        return failure_response(
            message="Only trainers can access this endpoint",
            data=None
        )
    
    user_service = UserService(session=session)
    user_data = user_service.get_user(current_user.id)
    return success_response(data=user_data, message="Trainer profile fetched successfully")


@router.get("/dashboard", response_model=APIResponse[DashboardKPIsResponse], status_code=status.HTTP_200_OK)
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get trainer dashboard KPIs"""
    if current_user.role != Role.TRAINER:
        return failure_response(
            message="Only trainers can access this endpoint",
            data=None
        )
    
    dashboard_service = DashboardService(session=session)
    kpis_data = dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=current_user.role,
        gym_id=current_user.gym_id
    )
    return success_response(data=kpis_data, message="Trainer dashboard KPIs fetched successfully")

