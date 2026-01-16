from fastapi import APIRouter, status
from sqlmodel import select
from app.core.permissions import require_any_authenticated
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.user import User
from app.models.role import Role as RoleModel
from app.schemas.membership import MembershipCreate, MembershipResponse
from app.schemas.billing import PaymentCreate, PaymentResponse
from app.schemas.attendance import MarkAttendanceRequest, MarkAttendanceResponse, CheckoutRequest, CheckoutResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.services.membership_service import MembershipService
from app.services.billing_service import BillingService
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/create", tags=["members"])


@router.post("/memberships", response_model=APIResponse[MembershipResponse], status_code=status.HTTP_201_CREATED)
def create_membership(
    membership: MembershipCreate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Create a membership for the current member"""
    # Get role name from database
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    
    if not role or role.name != "MEMBER":
        return failure_response(
            message="Only members can create memberships for themselves",
            data=None
        )
    
    if membership.user_id != current_user.id:
        return failure_response(
            message="You can only create memberships for yourself",
            data=None
        )
    
    membership_service = MembershipService(session=session)
    membership_data = membership_service.create_membership(membership)
    return success_response(data=membership_data, message="Membership created successfully")


@router.post("/payments", response_model=APIResponse[PaymentResponse], status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Create a payment for the current member"""
    # Get role name from database
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    
    if not role or role.name != "MEMBER":
        return failure_response(
            message="Only members can create payments for themselves",
            data=None
        )
    
    if payment.user_id != current_user.id:
        return failure_response(
            message="You can only create payments for yourself",
            data=None
        )
    
    billing_service = BillingService(session=session)
    payment_data = billing_service.create_payment(payment)
    return success_response(data=payment_data, message="Payment created successfully")


@router.post("/attendance", response_model=APIResponse[MarkAttendanceResponse], status_code=status.HTTP_201_CREATED)
def mark_attendance(
    request: MarkAttendanceRequest,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Mark attendance for the current member"""
    # Get role name from database
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    
    if not role or role.name != "MEMBER":
        return failure_response(
            message="Only members can mark attendance",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    attendance_service = AttendanceService(session=session)
    try:
        attendance_data = attendance_service.mark_attendance(
            user_id=current_user.id,
            request=request
        )
        return success_response(
            data=attendance_data, 
            message="Attendance marked successfully"
        )
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.post("/checkout", response_model=APIResponse[CheckoutResponse], status_code=status.HTTP_200_OK)
def checkout(
    request: CheckoutRequest,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Checkout for the current member"""
    if not request.checkout:
        return failure_response(
            message="checkout must be true",
            data=None,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Get role name from database
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    
    if not role or role.name != "MEMBER":
        return failure_response(
            message="Only members can checkout",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    attendance_service = AttendanceService(session=session)
    try:
        checkout_data = attendance_service.checkout(user_id=current_user.id)
        return success_response(
            data=checkout_data,
            message="Checkout successful"
        )
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )

