from fastapi import APIRouter, status
from sqlmodel import select
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
def create_bank_account(
    bank_account: BankAccountCreate,
    session: SessionDep = None,
    current_user: User = require_admin  # Only owners can create bank accounts
):
    """Create a new bank account for the owner's gym"""
    bank_account_service = BankAccountService(session=session)
    try:
        gym_id = get_user_gym_id(current_user, session)
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
def update_bank_account(
    bank_account_id: str,
    bank_account_update: BankAccountUpdate,
    session: SessionDep = None,
    current_user: User = require_admin  # Only owners can update bank accounts
):
    """Update a bank account (only if it belongs to the owner's gym)"""
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
