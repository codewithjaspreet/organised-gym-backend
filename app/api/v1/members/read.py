from fastapi import APIRouter, HTTPException
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.user import UserResponse
from app.schemas.membership import MembershipResponse
from app.schemas.billing import PaymentResponse
from app.schemas.dashboard import DashboardKPIsResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response
from app.services.user_service import UserService
from app.services.membership_service import MembershipService
from app.services.billing_service import BillingService
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/read", tags=["members"])


@router.get("/profile", response_model=APIResponse[UserResponse])
def get_member_profile(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get member profile"""
    if current_user.role != Role.MEMBER:
        raise HTTPException(
            status_code=403,
            detail="Only members can access this endpoint"
        )
    
    user_service = UserService(session=session)
    user_data = user_service.get_user(current_user.id)
    return success_response(data=user_data, message="Member profile fetched successfully")


@router.get("/dashboard", response_model=APIResponse[DashboardKPIsResponse])
def get_dashboard_kpis(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get member dashboard KPIs"""
    if current_user.role != Role.MEMBER:
        raise HTTPException(
            status_code=403,
            detail="Only members can access this endpoint"
        )
    
    dashboard_service = DashboardService(session=session)
    kpis_data = dashboard_service.get_user_kpis(
        user_id=current_user.id,
        role=current_user.role,
        gym_id=current_user.gym_id
    )
    return success_response(data=kpis_data, message="Member dashboard KPIs fetched successfully")


@router.get("/memberships/{membership_id}", response_model=APIResponse[MembershipResponse])
def get_membership(
    membership_id: str,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get a membership by ID (own memberships only)"""
    if current_user.role != Role.MEMBER:
        raise HTTPException(
            status_code=403,
            detail="Only members can access this endpoint"
        )
    
    membership_service = MembershipService(session=session)
    membership = membership_service.get_membership(membership_id)
    
    if membership.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own memberships"
        )
    
    return success_response(data=membership, message="Membership fetched successfully")


@router.get("/payments/{payment_id}", response_model=APIResponse[PaymentResponse])
def get_payment(
    payment_id: str,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get a payment by ID (own payments only)"""
    if current_user.role != Role.MEMBER:
        raise HTTPException(
            status_code=403,
            detail="Only members can access this endpoint"
        )
    
    billing_service = BillingService(session=session)
    payment = billing_service.get_payment(payment_id)
    
    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own payments"
        )
    
    return success_response(data=payment, message="Payment fetched successfully")

