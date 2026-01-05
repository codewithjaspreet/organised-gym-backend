from fastapi import APIRouter, status, Depends
from app.core.permissions import require_any_authenticated, require_admin, check_ownership_or_admin
from app.db.db import SessionDep
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.dashboard import DashboardKPIsResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.dashboard_service import DashboardService
from app.core.exceptions import UserNotFoundError, UserNameAlreadyExistsError, NotFoundError

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    try:
        user_service = UserService(session=session)
        user_data = user_service.create_user(user)
        return success_response(data=user_data, message="User created successfully")
    except UserNameAlreadyExistsError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Username already exists",
            status_code=status.HTTP_400_BAD_REQUEST
        )

@router.get("/{user_id}", response_model=APIResponse[UserResponse])
def get_user(
    user_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    check_ownership_or_admin(user_id, current_user, session)
    try:
        user_service = UserService(session=session)
        user_data = user_service.get_user(user_id)
        return success_response(data=user_data, message="User data fetched successfully")
    except UserNotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "User not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

@router.put("/{user_id}", response_model=APIResponse[UserResponse])
def update_user(
    user_id: str,
    user: UserUpdate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    check_ownership_or_admin(user_id, current_user, session)
    try:
        user_service = UserService(session=session)
        updated_user = user_service.update_user(user_id, user)
        return success_response(data=updated_user, message="User updated successfully")
    except UserNotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "User not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

@router.delete("/{user_id}", response_model=APIResponse[dict])
def delete_user(
    user_id: str,
    session: SessionDep,
    current_user: User = require_admin
):
    try:
        user_service = UserService(session=session)
        user_service.delete_user(user_id)
        return success_response(data=None, message="User deleted successfully")
    except UserNotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "User not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.get("/dashboard/kpis", response_model=APIResponse[DashboardKPIsResponse])
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
    from sqlmodel import select
    from app.models.role import Role as RoleModel
    from app.models.user import RoleEnum
    
    # Get role name from role_id
    if not current_user.role_id:
        return failure_response(
            message="User has no role assigned",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    if not role:
        return failure_response(
            message="User role not found",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Convert role name to RoleEnum
    try:
        user_role = RoleEnum(role.name)
    except ValueError:
        return failure_response(
            message=f"Invalid role: {role.name}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    dashboard_service = DashboardService(session=session)
    kpis_data = dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=user_role,
        gym_id=current_user.gym_id
    )
    return success_response(data=kpis_data, message="Dashboard KPIs fetched successfully")

