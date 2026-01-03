from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permissions import require_admin_or_staff
from app.db.db import SessionDep
from app.models.user import User, Role
from app.models.billing import Payment
from app.schemas.user import UserResponse
from app.schemas.billing import PaymentResponse
from app.schemas.dashboard import DashboardKPIsResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.billing_service import BillingService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/read", tags=["staff"])


def get_staff_gym(current_user: User, session: SessionDep):
    """Helper function to get the gym for the current staff user"""
    if not current_user.gym_id:
        return None
    return current_user.gym_id


@router.get("/profile", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def get_staff_profile(
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Get staff profile"""
    if current_user.role != Role.STAFF:
        return failure_response(
            message="Only staff can access this endpoint",
            data=None
        )
    
    user_service = UserService(session=session)
    user_data = user_service.get_user(current_user.id)
    return success_response(data=user_data, message="Staff profile fetched successfully")


@router.get("/dashboard", response_model=APIResponse[DashboardKPIsResponse], status_code=status.HTTP_200_OK)
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Get staff dashboard KPIs"""
    if current_user.role != Role.STAFF:
        return failure_response(
            message="Only staff can access this endpoint",
            data=None
        )
    
    dashboard_service = DashboardService(session=session)
    kpis_data = dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=current_user.role,
        gym_id=current_user.gym_id
    )
    return success_response(data=kpis_data, message="Staff dashboard KPIs fetched successfully")


@router.get("/payments/{payment_id}", response_model=APIResponse[PaymentResponse], status_code=status.HTTP_200_OK)
def get_payment(
    payment_id: str,
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Get a payment by ID (payments in staff's gym only)"""
    if current_user.role != Role.STAFF:
        return failure_response(
            message="Only staff can access this endpoint",
            data=None
        )
    
    gym_id = get_staff_gym(current_user, session)
    if not gym_id:
        return failure_response(
            message="No gym assigned to this staff member",
            data=None
        )
    
    billing_service = BillingService(session=session)
    payment = billing_service.get_payment(payment_id)
    
    if payment.gym_id != gym_id:
        return failure_response(
            message="Payment does not belong to your gym",
            data=None
        )
    
    return success_response(data=payment, message="Payment fetched successfully")

