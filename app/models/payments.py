from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.gym import Gym
    from app.models.membership import Membership
    from app.models.user import User


class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    
    id: str = Field(
        description="The payment id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    user_id: str = Field(
        description="The user id",
        foreign_key="users.id"
    )
    verified_by: Optional[str] = Field(
        description="The user id who verified the payment",
        foreign_key="users.id",
        nullable=True
    )
    amount: Decimal = Field(description="The payment amount")
    proof_url: Optional[str] = Field(
        description="The payment proof URL",
        nullable=True
    )
    status: str = Field(description="The payment status")
    created_at: datetime = Field(
        description="The payment creation date",
        default_factory=datetime.now
    )
    membership_id: str = Field(
        description="The membership id",
        foreign_key="memberships.id"
    )
    gym_id: str = Field(
        description="The gym id",
        foreign_key="gyms.id"
    )
    
    # Relationships
    user: Optional["User"] = Relationship(
        back_populates="payments",
        sa_relationship_kwargs={"foreign_keys": "[Payment.user_id]"}
    )
    verifier: Optional["User"] = Relationship(
        back_populates="verified_payments",
        sa_relationship_kwargs={"foreign_keys": "[Payment.verified_by]"}
    )
    membership: Optional["Membership"] = Relationship(back_populates="payments")
    gym: Optional["Gym"] = Relationship(back_populates="payments")

