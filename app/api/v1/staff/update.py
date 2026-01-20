from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permissions import require_admin_or_staff
from app.db.db import SessionDep
from app.models.user import User, Role
from app.models.payments import Payment
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.payments import PaymentResponse, PaymentUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.user_service import UserService
from app.services.payment import PaymentService

router = APIRouter(prefix="/update", tags=["staff"])


def get_staff_gym(current_user: User, session: SessionDep):
    """Helper function to get the gym for the current staff user"""
    if not current_user.gym_id:
        return None
    return current_user.gym_id


@router.put("/profile", response_model=APIResponse[UserResponse], status_code=status.HTTP_200_OK)
def update_staff_profile(
    user: UserUpdate,
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Update staff profile"""
    if current_user.role != Role.STAFF:
        return failure_response(
            message="Only staff can access this endpoint",
            data=None
        )
    
    user_service = UserService(session=session)
    updated_user = user_service.update_user(current_user.id, user)
    return success_response(data=updated_user, message="Staff profile updated successfully")


@router.put("/payments/{payment_id}", response_model=APIResponse[PaymentResponse], status_code=status.HTTP_200_OK)
def update_payment(
    payment_id: str,
    payment: PaymentUpdate,
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Update/verify a payment (staff can verify payments in their gym)"""
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
    
    billing_service = PaymentService(session=session)
    existing_payment = billing_service.get_payment(payment_id)
    
    if existing_payment.gym_id != gym_id:
        return failure_response(
            message="Payment does not belong to your gym",
            data=None
        )
    
    updated_payment = billing_service.update_payment(payment_id, payment)
    return success_response(data=updated_payment, message="Payment updated successfully")

