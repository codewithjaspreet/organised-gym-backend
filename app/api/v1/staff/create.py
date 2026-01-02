from fastapi import APIRouter, status, HTTPException
from sqlmodel import select
from app.core.permissions import require_admin_or_staff
from app.db.db import SessionDep
from app.models.user import User, Role
from app.models.billing import Payment
from app.schemas.billing import PaymentCreate, PaymentResponse
from app.services.billing_service import BillingService

router = APIRouter(prefix="/create", tags=["staff"])


def get_staff_gym(current_user: User, session: SessionDep):
    """Helper function to get the gym for the current staff user"""
    if not current_user.gym_id:
        raise HTTPException(
            status_code=404,
            detail="No gym assigned to this staff member"
        )
    return current_user.gym_id


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    session: SessionDep = None,
    current_user: User = require_admin_or_staff
):
    """Create a payment (staff can create payments for members in their gym)"""
    if current_user.role != Role.STAFF:
        raise HTTPException(
            status_code=403,
            detail="Only staff can access this endpoint"
        )
    
    gym_id = get_staff_gym(current_user, session)
    
    # Verify the payment is for a member in the same gym
    from app.models.user import User as UserModel
    user_stmt = select(UserModel).where(
        UserModel.id == payment.user_id,
        UserModel.gym_id == gym_id
    )
    user = session.exec(user_stmt).first()
    if not user:
        raise HTTPException(
            status_code=403,
            detail="User does not belong to your gym"
        )
    
    billing_service = BillingService(session=session)
    return billing_service.create_payment(payment)

