from datetime import datetime
from typing import List
from sqlmodel import select
from app.core.exceptions import NotFoundError
from app.db.db import SessionDep
from app.models.bank_account import BankAccount
from app.models.user import User
from app.schemas.bank_account import (
    BankAccountCreate,
    BankAccountUpdate,
    BankAccountResponse,
    BankAccountListResponse
)


class BankAccountService:

    def __init__(self, session: SessionDep):
        self.session = session

    def create_bank_account(
        self,
        user_id: str,
        bank_account: BankAccountCreate
    ) -> BankAccountResponse:
        """Create a new bank account for a user"""
        # Verify user exists
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise NotFoundError(detail=f"User with id {user_id} not found")

        db_bank_account = BankAccount(
            user_id=user_id,
            account_holder_name=bank_account.account_holder_name,
            bank_name=bank_account.bank_name,
            account_number=bank_account.account_number,
            ifsc_code=bank_account.ifsc_code,
            upi_id=bank_account.upi_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.session.add(db_bank_account)
        self.session.commit()
        self.session.refresh(db_bank_account)

        return BankAccountResponse.model_validate(db_bank_account.model_dump())

    def get_bank_account(self, bank_account_id: str) -> BankAccountResponse:
        """Get a bank account by ID"""
        stmt = select(BankAccount).where(BankAccount.id == bank_account_id)
        bank_account = self.session.exec(stmt).first()
        if not bank_account:
            raise NotFoundError(detail=f"Bank account with id {bank_account_id} not found")

        return BankAccountResponse.model_validate(bank_account.model_dump())

    def get_user_bank_accounts(self, user_id: str) -> BankAccountListResponse:
        """Get all bank accounts for a user"""
        # Verify user exists
        stmt = select(User).where(User.id == user_id)
        user = self.session.exec(stmt).first()
        if not user:
            raise NotFoundError(detail=f"User with id {user_id} not found")

        stmt = select(BankAccount).where(BankAccount.user_id == user_id).order_by(BankAccount.created_at.desc())
        bank_accounts = self.session.exec(stmt).all()

        bank_account_responses = [
            BankAccountResponse.model_validate(account.model_dump())
            for account in bank_accounts
        ]

        return BankAccountListResponse(bank_accounts=bank_account_responses)

    def update_bank_account(
        self,
        bank_account_id: str,
        bank_account_update: BankAccountUpdate
    ) -> BankAccountResponse:
        """Update a bank account"""
        stmt = select(BankAccount).where(BankAccount.id == bank_account_id)
        bank_account = self.session.exec(stmt).first()
        if not bank_account:
            raise NotFoundError(detail=f"Bank account with id {bank_account_id} not found")

        # Update only provided fields
        update_data = bank_account_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bank_account, field, value)

        # Update the updated_at timestamp
        bank_account.updated_at = datetime.now()

        self.session.commit()
        self.session.refresh(bank_account)

        return BankAccountResponse.model_validate(bank_account.model_dump())

    def delete_bank_account(self, bank_account_id: str) -> None:
        """Delete a bank account"""
        stmt = select(BankAccount).where(BankAccount.id == bank_account_id)
        bank_account = self.session.exec(stmt).first()
        if not bank_account:
            raise NotFoundError(detail=f"Bank account with id {bank_account_id} not found")

        self.session.delete(bank_account)
        self.session.commit()
        return None
