from fastapi import (
    APIRouter,
    HTTPException,
    status,
    File,
    UploadFile,
    Form,
    Request,
    BackgroundTasks,
)
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
from app.schemas.attendance import (
    MarkAttendanceRequest,
    MarkAttendanceResponse,
    CheckoutRequest,
    CheckoutResponse
)
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.utils.cloudinary import get_cloudinary_service
from app.services.membership_service import MembershipService
from app.services.payment import PaymentService
from app.services.attendance_service import AttendanceService
from app.services.user_service import UserService
from app.utils.emails import send_reset_password_mail, send_password_reset_confirmation_mail

router = APIRouter(prefix="/create", tags=["Members"])


# -------------------- MEMBERSHIP --------------------

@router.post(
    "/memberships",
    response_model=APIResponse[MembershipResponse],
    status_code=status.HTTP_201_CREATED
)
def create_membership(
    membership: MembershipCreate,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
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

    return success_response(
        data=membership_data,
        message="Membership created successfully"
    )


# -------------------- PAYMENTS --------------------

@router.post(
    "/payments",
    response_model=APIResponse[PaymentResponseSchema],
    status_code=status.HTTP_201_CREATED
)
async def create_payment(
    session: SessionDep,
    current_user: User = require_any_authenticated,
    plan_id: str = Form(...),
    proof_file: UploadFile = File(...),
    remarks: Optional[str] = Form(None),
):
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()

    if not role or role.name != "MEMBER":
        return failure_response(
            message="Only members can create payments",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )

    if not current_user.gym_id:
        return failure_response(
            message="No gym assigned to this member",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )

    cloudinary_service = get_cloudinary_service()
    proof_url = await cloudinary_service.upload_image(
        file=proof_file,
        folder=f"payments/{current_user.gym_id}",
        public_id=f"payment_{current_user.id}_{plan_id}_{int(time.time())}",
        optimize=True
    )

    payment_data = MemberPaymentCreate(
        plan_id=plan_id,
        proof_url=proof_url,
        remarks=remarks
    )

    payment_service = PaymentService(session=session)
    payment_result = payment_service.create_member_payment(
        user_id=current_user.id,
        payment_data=payment_data
    )

    return success_response(
        data=payment_result,
        message="Payment created successfully"
    )


# -------------------- ATTENDANCE --------------------

@router.post(
    "/attendance",
    response_model=APIResponse[MarkAttendanceResponse],
    status_code=status.HTTP_201_CREATED
)
def mark_attendance(
    request: MarkAttendanceRequest,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()

    if not role or role.name != "MEMBER":
        return failure_response(
            message="Only members can mark attendance",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )

    attendance_service = AttendanceService(session=session)
    attendance_data = attendance_service.mark_attendance(
        user_id=current_user.id,
        request=request
    )

    return success_response(
        data=attendance_data,
        message="Attendance marked successfully"
    )


# -------------------- CHECKOUT --------------------

@router.post(
    "/checkout",
    response_model=APIResponse[CheckoutResponse],
    status_code=status.HTTP_200_OK
)
def checkout(
    request: CheckoutRequest,
    session: SessionDep,
    current_user: User = require_any_authenticated
):
    if not request.checkout:
        return failure_response(
            message="checkout must be true",
            data=None,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    stmt = select(RoleModel).where(RoleModel.id == current_user.role_id)
    role = session.exec(stmt).first()

    if not role or role.name != "MEMBER":
        return failure_response(
            message="Only members can checkout",
            data=None,
            status_code=status.HTTP_403_FORBIDDEN
        )

    attendance_service = AttendanceService(session=session)
    checkout_data = attendance_service.checkout(user_id=current_user.id)

    return success_response(
        data=checkout_data,
        message="Checkout successful"
    )


# -------------------- FORGOT PASSWORD --------------------

@router.post(
    "/forgot-password",
    summary="Trigger forgot password email",
    status_code=status.HTTP_200_OK
)
def forgot_password(
    request: Request,
    session: SessionDep,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
):
    reset_data = UserService(session).get_reset_link_data(
        email=email,
        base_url=str(request.base_url),
    )
    if reset_data:
        background_tasks.add_task(send_reset_password_mail, *reset_data)

    return success_response(
        message="If the email exists, a reset link has been sent.",
        data=None
    )


# -------------------- RESET PASSWORD --------------------

@router.post(
    "/reset-password",
    summary="Reset password using token",
    status_code=status.HTTP_200_OK
)
def reset_password(
    session: SessionDep,
    background_tasks: BackgroundTasks,
    token: str = Form(...),
    new_password: str = Form(...),
):
    try:
        user = UserService(session).reset_password(
            token=token,
            new_password=new_password,
        )
        background_tasks.add_task(
            send_password_reset_confirmation_mail,
            user.email,
            user.name,
        )
        return success_response(
            message="Password reset successful",
            data=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
