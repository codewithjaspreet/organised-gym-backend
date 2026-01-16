from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role, RoleEnum
from app.models.role import Role as RoleModel
from app.schemas.user import UserResponse
from app.schemas.membership import MembershipResponse
from app.schemas.billing import PaymentResponse
from app.schemas.dashboard import DashboardKPIsResponse
from app.schemas.gym import GymResponse
from app.schemas.plan import PlanResponse, PlanListResponse
from app.schemas.gym_rule import GymRuleResponse, GymRuleListResponse
from app.schemas.attendance import ActiveCheckInStatusResponse
from app.services.attendance_service import AttendanceService
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.membership_service import MembershipService
from app.services.billing_service import BillingService
from app.services.dashboard_service import DashboardService
from app.services.gym_service import GymService
from app.services.plan_service import PlanService

router = APIRouter(prefix="/read", tags=["members"])


@router.get("/profile", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def get_member_profile(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get member profile"""
    if current_user.role != Role.MEMBER:
        return failure_response(
            message="Only members can access this endpoint",
            data=None
        )
    
    user_service = UserService(session=session)
    user_data = user_service.get_user(current_user.id)
    return success_response(data=user_data, message="Member profile fetched successfully")


@router.get("/dashboard", response_model=APIResponse[DashboardKPIsResponse], status_code=status.HTTP_200_OK)
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get member dashboard KPIs"""
    # Get role name from database
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    if not role:
        return failure_response(
            message="User role not found",
            data=None
        )
    
    # Verify user is a MEMBER
    if role.name != "MEMBER":
        return failure_response(
            message="Only members can access this endpoint",
            data=None
        )
    
    role_enum = RoleEnum(role.name)
    
    dashboard_service = DashboardService(session=session)
    kpis_data = dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=role_enum,
        gym_id=current_user.gym_id
    )
    return success_response(data=kpis_data, message="Member dashboard KPIs fetched successfully")


@router.get("/memberships/{membership_id}", response_model=APIResponse[MembershipResponse], status_code=status.HTTP_200_OK)
def get_membership(
    membership_id: str,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get a membership by ID (own memberships only)"""
    if current_user.role != Role.MEMBER:
        return failure_response(
            message="Only members can access this endpoint",
            data=None
        )
    
    membership_service = MembershipService(session=session)
    membership = membership_service.get_membership(membership_id)
    
    if membership.user_id != current_user.id:
        return failure_response(
            message="You can only access your own memberships",
            data=None
        )
    
    return success_response(data=membership, message="Membership fetched successfully")


@router.get("/payments/{payment_id}", response_model=APIResponse[PaymentResponse], status_code=status.HTTP_200_OK)
def get_payment(
    payment_id: str,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get a payment by ID (own payments only)"""
    if current_user.role != Role.MEMBER:
        return failure_response(
            message="Only members can access this endpoint",
            data=None
        )
    
    billing_service = BillingService(session=session)
    payment = billing_service.get_payment(payment_id)
    
    if payment.user_id != current_user.id:
        return failure_response(
            message="You can only access your own payments",
            data=None
        )
    
    return success_response(data=payment, message="Payment fetched successfully")


@router.get("/gym", response_model=APIResponse[GymResponse], status_code=status.HTTP_200_OK)
def get_member_gym_info(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get member's gym information"""
    # Get role name from database (same pattern as dashboard endpoint)
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    if not role:
        return failure_response(
            message="User role not found",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Verify user is a MEMBER
    if role.name != "MEMBER":
        return failure_response(
            message="Only members can access this endpoint",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check if member has a gym assigned
    if not current_user.gym_id:
        return failure_response(
            message="No gym assigned to this member",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    gym_service = GymService(session=session)
    try:
        gym_data = gym_service.get_gym(current_user.gym_id)
        return success_response(data=gym_data, message="Gym information fetched successfully")
    except Exception as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else "Gym not found",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.get("/plans", response_model=APIResponse[PlanListResponse], status_code=status.HTTP_200_OK)
def get_all_plans(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get all plans for the member's gym"""
    # Get role name from database
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    if not role:
        return failure_response(
            message="User role not found",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Verify user is a MEMBER
    if role.name != "MEMBER":
        return failure_response(
            message="Only members can access this endpoint",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check if member has a gym assigned
    if not current_user.gym_id:
        return failure_response(
            message="No gym assigned to this member",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    plan_service = PlanService(session=session)
    plans_data = plan_service.get_all_plans(gym_id=current_user.gym_id)
    return success_response(data=plans_data, message="Plans fetched successfully")


@router.get("/rules", response_model=APIResponse[GymRuleListResponse], status_code=status.HTTP_200_OK)
def get_all_gym_rules(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get all gym rules for the member's gym"""
    # Get role name from database
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    if not role:
        return failure_response(
            message="User role not found",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Verify user is a MEMBER
    if role.name != "MEMBER":
        return failure_response(
            message="Only members can access this endpoint",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check if member has a gym assigned
    if not current_user.gym_id:
        return failure_response(
            message="No gym assigned to this member",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    gym_service = GymService(session=session)
    rules_data = gym_service.get_all_gym_rules(gym_id=current_user.gym_id)
    return success_response(data=rules_data, message="Gym rules fetched successfully")


@router.get("/checkin-status", response_model=APIResponse[ActiveCheckInStatusResponse], status_code=status.HTTP_200_OK)
def get_checkin_status(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get active check-in status for the current member"""
    # Get role name from database
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    
    if not role or role.name != "MEMBER":
        return failure_response(
            message="Only members can check their check-in status",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    attendance_service = AttendanceService(session=session)
    status_data = attendance_service.has_active_checkin(user_id=current_user.id)
    return success_response(data=status_data, message="Check-in status fetched successfully")

