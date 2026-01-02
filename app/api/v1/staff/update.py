from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.core.permissions import require_admin_or_staff
from app.db.db import SessionDep
from app.models.user import User, Role
from app.models.billing import Payment
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.billing import PaymentResponse, PaymentUpdate
from app.services.user_service import UserService
from app.services.billing_service import BillingService

router = APIRouter(prefix="/update", tags=["staff"])


def get_staff_gym(current_user: User, session: SessionDep):
    """Helper function to get the gym for the current staff user"""
    if not current_user.gym_id:
        raise HTTPException(
            status_code=404,
            detail="No gym assigned to this staff member"
        )
    return current_user.gym_id


@router.put("/profile", response_model=UserResponse)
def update_staff_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Update staff profile"""
    if current_user.role != Role.STAFF:
        raise HTTPException(
            status_code=403,
            detail="Only staff can access this endpoint"
        )
    
    user_service = UserService(session=session)
    return user_service.update_user(current_user.id, user)


@router.put("/payments/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: str,
    payment: PaymentUpdate,
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Update/verify a payment (staff can verify payments in their gym)"""
    if current_user.role != Role.STAFF:
        raise HTTPException(
            status_code=403,
            detail="Only staff can access this endpoint"
        )
    
    gym_id = get_staff_gym(current_user, session)
    billing_service = BillingService(session=session)
    existing_payment = billing_service.get_payment(payment_id)
    
    if existing_payment.gym_id != gym_id:
        raise HTTPException(
            status_code=403,
            detail="Payment does not belong to your gym"
        )
    
    return billing_service.update_payment(payment_id, payment)

