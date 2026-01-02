from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.core.permissions import require_admin_or_staff
from app.db.db import SessionDep
from app.models.user import User, Role
from app.models.billing import Payment
from app.schemas.user import UserResponse
from app.schemas.billing import PaymentResponse
from app.schemas.dashboard import DashboardKPIsResponse
from app.services.user_service import UserService
from app.services.billing_service import BillingService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/read", tags=["staff"])


def get_staff_gym(current_user: User, session: SessionDep):
    """Helper function to get the gym for the current staff user"""
    if not current_user.gym_id:
        raise HTTPException(
            status_code=404,
            detail="No gym assigned to this staff member"
        )
    return current_user.gym_id


@router.get("/profile", response_model=UserResponse)
def get_staff_profile(
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Get staff profile"""
    if current_user.role != Role.STAFF:
        raise HTTPException(
            status_code=403,
            detail="Only staff can access this endpoint"
        )
    
    user_service = UserService(session=session)
    return user_service.get_user(current_user.id)


@router.get("/dashboard", response_model=DashboardKPIsResponse)
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Get staff dashboard KPIs"""
    if current_user.role != Role.STAFF:
        raise HTTPException(
            status_code=403,
            detail="Only staff can access this endpoint"
        )
    
    dashboard_service = DashboardService(session=session)
    return dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=current_user.role,
        gym_id=current_user.gym_id
    )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Get a payment by ID (payments in staff's gym only)"""
    if current_user.role != Role.STAFF:
        raise HTTPException(
            status_code=403,
            detail="Only staff can access this endpoint"
        )
    
    gym_id = get_staff_gym(current_user, session)
    billing_service = BillingService(session=session)
    payment = billing_service.get_payment(payment_id)
    
    if payment.gym_id != gym_id:
        raise HTTPException(
            status_code=403,
            detail="Payment does not belong to your gym"
        )
    
    return payment

