from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4


if TYPE_CHECKING:
    from app.models.attendance import Attendance
    from app.models.payments import Payment
    from app.models.gym_subscription import GymSubscription
    from app.models.membership import Membership
    from app.models.plan import Plan
    from app.models.user import User
    from app.models.announcement import Announcement
    from app.models.gym_rule import GymRule
    from app.models.bank_account import BankAccount


class Gym(SQLModel, table=True):
    __tablename__ = "gyms"
    
    id: str = Field(
        description="The gym's id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    owner_id: str = Field(
        description="The owner's user id",
        foreign_key="users.id"
    )
    name: str = Field(description="The gym's name", min_length=1)
    logo: Optional[str] = Field(
        description="The gym's logo URL",
        nullable=True
    )
    address_line1: str = Field(description="The gym's address line 1", min_length=4)
    address_line2: Optional[str] = Field(
        description="The gym's address line 2",
        nullable=True
    )
    city: str = Field(description="The gym's city", min_length=4)
    state: str = Field(description="The gym's state", min_length=4)
    postal_code: str = Field(description="The gym's postal code")
    dob: Optional[str] = Field(
        description="The gym's date of birth",
        nullable=True
    )
    country: str = Field(description="The gym's country", min_length=4)
    opening_hours: Optional[str] = Field(
        description="The gym's opening hours",
        nullable=True
    )
    is_active: bool = Field(
        description="Whether the gym is active",
        default=True
    )
    gym_code: Optional[str] = Field(
        description="The gym's unique 6-letter code",
        nullable=True,
        unique=True,
        index=True
    )
    whatsapp_number: Optional[str] = Field(
        description="The gym's WhatsApp number",
        nullable=True
    )
    mobile_no: Optional[str] = Field(
        description="The gym's mobile number",
        nullable=True
    )
    website: Optional[str] = Field(
        description="The gym's website URL",
        nullable=True
    )
    email: Optional[str] = Field(
        description="The gym's email address",
        nullable=True
    )
    insta: Optional[str] = Field(
        description="The gym's Instagram handle/URL",
        nullable=True
    )
    facebook: Optional[str] = Field(
        description="The gym's Facebook page URL",
        nullable=True
    )
    youtube: Optional[str] = Field(
        description="The gym's YouTube channel URL",
        nullable=True
    )
    twitter: Optional[str] = Field(
        description="The gym's Twitter handle/URL",
        nullable=True
    )
    created_at: datetime = Field(
        description="The gym's creation date",
        default_factory=datetime.now
    )
    
    # Relationships
    owner: Optional["User"] = Relationship(
        back_populates="owned_gyms",
        sa_relationship_kwargs={"foreign_keys": "[Gym.owner_id]"}
    )
    members: List["User"] = Relationship(
        back_populates="gym",
        sa_relationship_kwargs={"foreign_keys": "[User.gym_id]"}
    )

    announcements:List["Announcement"] = Relationship(back_populates="gym")
    attendances: List["Attendance"] = Relationship(back_populates="gym")
    payments: List["Payment"] = Relationship(back_populates="gym")
    memberships: List["Membership"] = Relationship(back_populates="gym")
    plans: List["Plan"] = Relationship(back_populates="gym")
    gym_subscriptions: List["GymSubscription"] = Relationship(back_populates="gym")
    rules: List["GymRule"] = Relationship(back_populates="gym")
    bank_accounts: List["BankAccount"] = Relationship(back_populates="gym")

