from fastapi import APIRouter, status, HTTPException
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User, Role
from app.schemas.membership import MembershipCreate, MembershipResponse
from app.schemas.billing import PaymentCreate, PaymentResponse
from app.services.membership_service import MembershipService
from app.services.billing_service import BillingService

router = APIRouter(prefix="/create", tags=["members"])


@router.post("/memberships", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
def create_membership(
    membership: MembershipCreate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Create a membership for the current member"""
    if current_user.role != Role.MEMBER:
        raise HTTPException(
            status_code=403,
            detail="Only members can create memberships for themselves"
        )
    
    if membership.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create memberships for yourself"
        )
    
    membership_service = MembershipService(session=session)
    return membership_service.create_membership(membership)


@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Create a payment for the current member"""
    if current_user.role != Role.MEMBER:
        raise HTTPException(
            status_code=403,
            detail="Only members can create payments for themselves"
        )
    
    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create payments for yourself"
        )
    
    billing_service = BillingService(session=session)
    return billing_service.create_payment(payment)

