from fastapi import APIRouter, status, File, UploadFile, Form
from sqlmodel import select
from typing import Optional
import time
from app.core.permissions import require_any_authenticated, require_admin
from app.db.db import SessionDep
from app.models.user import User
from app.models.bank_account import BankAccount
from app.models.gym import Gym
from app.schemas.bank_account import (
    BankAccountCreate,
    BankAccountUpdate,
    BankAccountResponse,
    BankAccountListResponse
)
from app.schemas.response import APIResponse
from app.utils.response import success_response, failure_response
from app.utils.cloudinary import get_cloudinary_service
from app.services.bank_account_service import BankAccountService
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/bank-accounts", tags=["bank-accounts"])


def get_user_gym_id(user: User, session: SessionDep) -> str:
    """Get gym_id for the user (member gets their gym, owner gets their owned gym)"""
    if user.gym_id:
        return user.gym_id
    
    # If user is owner/admin, get their owned gym
    stmt = select(Gym).where(Gym.owner_id == user.id)
    gym = session.exec(stmt).first()
    if gym:
        return gym.id
    
    raise NotFoundError(detail="No gym found for this user")


@router.get("/", response_model=APIResponse[BankAccountListResponse], status_code=status.HTTP_200_OK)
def get_bank_accounts(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get all bank accounts for the user's gym (members can see gym bank accounts)"""
    bank_account_service = BankAccountService(session=session)
    try:
        gym_id = get_user_gym_id(current_user, session)
        bank_accounts_data = bank_account_service.get_gym_bank_accounts(gym_id=gym_id)
        return success_response(
            data=bank_accounts_data,
            message="Bank accounts fetched successfully"
        )
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.get("/{bank_account_id}", response_model=APIResponse[BankAccountResponse], status_code=status.HTTP_200_OK)
def get_bank_account(
    bank_account_id: str,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get a specific bank account by ID (must belong to user's gym)"""
    # Get user's gym_id
    gym_id = get_user_gym_id(current_user, session)
    
    # Verify the bank account belongs to the user's gym
    stmt = select(BankAccount).where(
        BankAccount.id == bank_account_id,
        BankAccount.gym_id == gym_id
    )
    bank_account = session.exec(stmt).first()
    
    if not bank_account:
        return failure_response(
            message="Bank account not found or access denied",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    bank_account_service = BankAccountService(session=session)
    try:
        bank_account_data = bank_account_service.get_bank_account(bank_account_id)
        return success_response(
            data=bank_account_data,
            message="Bank account fetched successfully"
        )
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.post("/", response_model=APIResponse[BankAccountResponse], status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    account_holder_name: str = Form(..., description="The account holder's name"),
    bank_name: str = Form(..., description="The bank name"),
    account_number: str = Form(..., description="The bank account number"),
    ifsc_code: str = Form(..., description="The IFSC code"),
    upi_id: Optional[str] = Form(None, description="The UPI ID"),
    qr_code_file: Optional[UploadFile] = File(None, description="The QR code image file"),
    session: SessionDep = None,
    current_user: User = require_admin  # Only owners can create bank accounts
):
    """Create a new bank account for the owner's gym with optional QR code upload"""
    bank_account_service = BankAccountService(session=session)
    try:
        gym_id = get_user_gym_id(current_user, session)
        
        # Handle QR code file upload if present
        qr_code_url = None
        if qr_code_file and qr_code_file.filename:
            cloudinary_service = get_cloudinary_service()
            try:
                qr_code_url = await cloudinary_service.upload_image(
                    file=qr_code_file,
                    folder=f"bank_accounts/{gym_id}",
                    public_id=f"qr_code_{gym_id}_{int(time.time())}",
                    optimize=True
                )
            except Exception as e:
                return failure_response(
                    message=f"Failed to upload QR code: {str(e)}",
                    data=None,
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        
        # Create bank account data object
        bank_account = BankAccountCreate(
            account_holder_name=account_holder_name,
            bank_name=bank_name,
            account_number=account_number,
            ifsc_code=ifsc_code,
            upi_id=upi_id,
            qr_code_url=qr_code_url
        )
        
        bank_account_data = bank_account_service.create_bank_account(
            gym_id=gym_id,
            bank_account=bank_account
        )
        return success_response(
            data=bank_account_data,
            message="Bank account created successfully"
        )
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.put("/{bank_account_id}", response_model=APIResponse[BankAccountResponse], status_code=status.HTTP_200_OK)
async def update_bank_account(
    bank_account_id: str,
    account_holder_name: Optional[str] = Form(None, description="The account holder's name"),
    bank_name: Optional[str] = Form(None, description="The bank name"),
    account_number: Optional[str] = Form(None, description="The bank account number"),
    ifsc_code: Optional[str] = Form(None, description="The IFSC code"),
    upi_id: Optional[str] = Form(None, description="The UPI ID"),
    qr_code_file: Optional[UploadFile] = File(None, description="The QR code image file (upload to Cloudinary)"),
    qr_code_url: Optional[str] = Form(None, description="The QR code URL (direct URL, alternative to file upload)"),
    session: SessionDep = None,
    current_user: User = require_admin  # Only owners can update bank accounts
):
    """Update a bank account (only if it belongs to the owner's gym) with optional QR code upload or URL"""
    # Get owner's gym_id
    gym_id = get_user_gym_id(current_user, session)
    
    # Verify the bank account belongs to the owner's gym
    stmt = select(BankAccount).where(
        BankAccount.id == bank_account_id,
        BankAccount.gym_id == gym_id
    )
    bank_account = session.exec(stmt).first()
    
    if not bank_account:
        return failure_response(
            message="Bank account not found or access denied",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Handle QR code - prioritize file upload over direct URL
    final_qr_code_url = None
    if qr_code_file and qr_code_file.filename:
        # Upload file to Cloudinary
        cloudinary_service = get_cloudinary_service()
        try:
            final_qr_code_url = await cloudinary_service.upload_image(
                file=qr_code_file,
                folder=f"bank_accounts/{gym_id}",
                public_id=f"qr_code_{bank_account_id}_{int(time.time())}",
                optimize=True
            )
        except Exception as e:
            return failure_response(
                message=f"Failed to upload QR code: {str(e)}",
                data=None,
                status_code=status.HTTP_400_BAD_REQUEST
            )
    elif qr_code_url:
        # Use direct URL if provided
        final_qr_code_url = qr_code_url
    
    # Build update data
    update_data = {}
    if account_holder_name is not None:
        update_data["account_holder_name"] = account_holder_name
    if bank_name is not None:
        update_data["bank_name"] = bank_name
    if account_number is not None:
        update_data["account_number"] = account_number
    if ifsc_code is not None:
        update_data["ifsc_code"] = ifsc_code
    if upi_id is not None:
        update_data["upi_id"] = upi_id
    if final_qr_code_url is not None:
        update_data["qr_code_url"] = final_qr_code_url
    
    # Create update object
    bank_account_update = BankAccountUpdate(**update_data)
    
    bank_account_service = BankAccountService(session=session)
    try:
        bank_account_data = bank_account_service.update_bank_account(
            bank_account_id=bank_account_id,
            bank_account_update=bank_account_update
        )
        return success_response(
            data=bank_account_data,
            message="Bank account updated successfully"
        )
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )


@router.delete("/{bank_account_id}", response_model=APIResponse[dict], status_code=status.HTTP_200_OK)
def delete_bank_account(
    bank_account_id: str,
    session: SessionDep = None,
    current_user: User = require_admin  # Only owners can delete bank accounts
):
    """Delete a bank account (only if it belongs to the owner's gym)"""
    # Get owner's gym_id
    gym_id = get_user_gym_id(current_user, session)
    
    # Verify the bank account belongs to the owner's gym
    stmt = select(BankAccount).where(
        BankAccount.id == bank_account_id,
        BankAccount.gym_id == gym_id
    )
    bank_account = session.exec(stmt).first()
    
    if not bank_account:
        return failure_response(
            message="Bank account not found or access denied",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    bank_account_service = BankAccountService(session=session)
    try:
        bank_account_service.delete_bank_account(bank_account_id)
        return success_response(
            data={},
            message="Bank account deleted successfully"
        )
    except NotFoundError as e:
        return failure_response(
            message=str(e.detail) if hasattr(e, 'detail') else str(e),
            data=None,
            status_code=status.HTTP_404_NOT_FOUND
        )
