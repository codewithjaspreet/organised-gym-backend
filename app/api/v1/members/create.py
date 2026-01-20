from fastapi import APIRouter, status, File, UploadFile, Form
from sqlmodel import select
from typing import Optional
import time
from app.core.permissions import require_any_authenticated
from app.core.exceptions import NotFoundError, AlreadyExistsError
from app.db.db import SessionDep
from app.models.user import User
from app.models.role import Role as RoleModel
from app.schemas.membership import MembershipCreate, MembershipResponse
from app.schemas.payments import MemberPaymentCreate, PaymentResponse as PaymentResponseSchema
from app.schemas.attendance import MarkAttendanceRequest, MarkAttendanceResponse, CheckoutRequest, CheckoutResponse
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.utils.cloudinary import get_cloudinary_service
from app.services.membership_service import MembershipService
from app.services.payment import PaymentService
from app.services.attendance_service import AttendanceService
from app.core.exceptions import NotFoundError

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


@router.post("/payments", response_model=APIResponse[PaymentResponseSchema], status_code=status.HTTP_201_CREATED)
async def create_payment(
    plan_id: str = Form(..., description="The plan id"),
    proof_file: UploadFile = File(..., description="The payment proof/screenshot file"),
    remarks: Optional[str] = Form(None, description="Payment remarks/notes"),
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Create a payment for the current member's plan with file upload"""
    # Get role name from database
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()
    
    if not role or role.name != "MEMBER":
        return failure_response(
            message="Only members can create payments",
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
    
    # Upload file to Cloudinary
    cloudinary_service = get_cloudinary_service()
    try:
        proof_url = await cloudinary_service.upload_image(
            file=proof_file,
            folder=f"payments/{current_user.gym_id}",
            public_id=f"payment_{current_user.id}_{plan_id}_{int(time.time())}",
            optimize=True
        )
    except Exception as e:
        return failure_response(
            message=f"Failed to upload payment proof: {str(e)}",
            data=None,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Create payment data object
    payment_data = MemberPaymentCreate(
        plan_id=plan_id,
        proof_url=proof_url,
        remarks=remarks
    )
    
    payment_service = PaymentService(session=session)
    try:
        payment_result = payment_service.create_member_payment(
            user_id=current_user.id,
            payment_data=payment_data
        )
        return success_response(data=payment_result, message="Payment created successfully")
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return failure_response(
            message=str(e),
            data=None,
            status_code=status.HTTP_400_BAD_REQUEST
        )


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
    except AlreadyExistsError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_400_BAD_REQUEST
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

