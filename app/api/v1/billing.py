from fastapi import APIRouter, status, HTTPException, Depends
from sqlmodel import select
from app.core.permissions import require_any_authenticated, require_admin, require_admin_or_staff, check_gym_ownership
from app.db.db import SessionDep
from app.models.user import User, Role
from app.models.billing import Payment
from app.schemas.billing import PaymentCreate, PaymentResponse, PaymentUpdate
from app.schemas.response import APIResponse
from app.utils.response import success_response
from app.services.billing_service import BillingService

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/", response_model=APIResponse[PaymentResponse], status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Members can create their own payments
    if payment.user_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create payments for yourself"
        )
    
    billing_service = BillingService(session=session)
    payment_data = billing_service.create_payment(payment)
    return success_response(data=payment_data, message="Payment created successfully")

@router.get("/{payment_id}", response_model=APIResponse[PaymentResponse])
def get_payment(
    payment_id: str,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    # Check if user owns payment or is gym admin/staff
    stmt = select(Payment).where(Payment.id == payment_id)
    db_payment = session.exec(stmt).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if current_user.role in [Role.ADMIN, Role.STAFF]:
        check_gym_ownership(db_payment.gym_id, current_user, session)
    elif db_payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own payments"
        )
    
    billing_service = BillingService(session=session)
    payment_data = billing_service.get_payment(payment_id)
    return success_response(data=payment_data, message="Payment fetched successfully")

@router.put("/{payment_id}", response_model=APIResponse[PaymentResponse])
def update_payment(
    payment_id: str,
    payment: PaymentUpdate,
    session: SessionDep,
    current_user: User = require_admin_or_staff
):
    # Only gym admin/staff can update payments (for verification)
    stmt = select(Payment).where(Payment.id == payment_id)
    db_payment = session.exec(stmt).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    check_gym_ownership(db_payment.gym_id, current_user, session)
    
    billing_service = BillingService(session=session)
    updated_payment = billing_service.update_payment(payment_id, payment)
    return success_response(data=updated_payment, message="Payment updated successfully")

@router.delete("/{payment_id}", response_model=APIResponse[dict])
def delete_payment(
    payment_id: str,
    session: SessionDep,
    current_user: User = require_admin
):
    # Only gym admin can delete payments
    stmt = select(Payment).where(Payment.id == payment_id)
    db_payment = session.exec(stmt).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    check_gym_ownership(db_payment.gym_id, current_user, session)
    
    billing_service = BillingService(session=session)
    billing_service.delete_payment(payment_id)
    return success_response(data=None, message="Payment deleted successfully")

