from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.gym import Gym


class BankAccount(SQLModel, table=True):
    __tablename__ = "bank_accounts"
    
    id: str = Field(
        description="The bank account id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    gym_id: str = Field(
        description="The gym id",
        foreign_key="gyms.id",
        index=True
    )
    user_id: Optional[str] = Field(
        description="The user id (optional, for future user-level accounts)",
        foreign_key="users.id",
        nullable=True,
        default=None
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
    gym: Optional["Gym"] = Relationship(back_populates="bank_accounts")
    user: Optional["User"] = Relationship(back_populates="bank_accounts")
