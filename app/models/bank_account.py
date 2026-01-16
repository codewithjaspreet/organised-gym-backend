from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.user import User


class BankAccount(SQLModel, table=True):
    __tablename__ = "bank_accounts"
    
    id: str = Field(
        description="The bank account id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    user_id: str = Field(
        description="The user id",
        foreign_key="users.id",
        index=True
    )
    account_holder_name: str = Field(
        description="The account holder's name",
        min_length=1
    )
    bank_name: str = Field(
        description="The bank name",
        min_length=1
    )
    account_number: str = Field(
        description="The bank account number",
        min_length=1
    )
    ifsc_code: str = Field(
        description="The IFSC code",
        min_length=1
    )
    upi_id: Optional[str] = Field(
        description="The UPI ID",
        nullable=True
    )
    created_at: datetime = Field(
        description="The bank account creation date",
        default_factory=datetime.now
    )
    updated_at: datetime = Field(
        description="The bank account last update date",
        default_factory=datetime.now
    )
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="bank_accounts")
