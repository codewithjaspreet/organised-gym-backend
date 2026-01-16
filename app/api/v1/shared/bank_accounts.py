from fastapi import APIRouter, status, Query
from sqlmodel import select
from typing import Optional
from app.core.permissions import require_any_authenticated
from app.db.db import SessionDep
from app.models.user import User
from app.models.bank_account import BankAccount
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


@router.post("/", response_model=APIResponse[BankAccountResponse], status_code=status.HTTP_201_CREATED)
def create_bank_account(
    bank_account: BankAccountCreate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Create a new bank account for the current user"""
    bank_account_service = BankAccountService(session=session)
    try:
        bank_account_data = bank_account_service.create_bank_account(
            user_id=current_user.id,
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


@router.get("/", response_model=APIResponse[BankAccountListResponse], status_code=status.HTTP_200_OK)
def get_user_bank_accounts(
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Get all bank accounts for the current user"""
    bank_account_service = BankAccountService(session=session)
    try:
        bank_accounts_data = bank_account_service.get_user_bank_accounts(
            user_id=current_user.id
        )
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
    """Get a specific bank account by ID (only if it belongs to the current user)"""
    # Verify the bank account belongs to the current user
    stmt = select(BankAccount).where(
        BankAccount.id == bank_account_id,
        BankAccount.user_id == current_user.id
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


@router.put("/{bank_account_id}", response_model=APIResponse[BankAccountResponse], status_code=status.HTTP_200_OK)
def update_bank_account(
    bank_account_id: str,
    bank_account_update: BankAccountUpdate,
    session: SessionDep = None,
    current_user: User = require_any_authenticated
):
    """Update a bank account (only if it belongs to the current user)"""
    # Verify the bank account belongs to the current user
    stmt = select(BankAccount).where(
        BankAccount.id == bank_account_id,
        BankAccount.user_id == current_user.id
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
    current_user: User = require_any_authenticated
):
    """Delete a bank account (only if it belongs to the current user)"""
    # Verify the bank account belongs to the current user
    stmt = select(BankAccount).where(
        BankAccount.id == bank_account_id,
        BankAccount.user_id == current_user.id
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
