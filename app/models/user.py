from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date
from uuid import uuid4


if TYPE_CHECKING:
    from app.models.attendance import Attendance
    from app.models.billing import Payment
    from app.models.gym import Gym
    from app.models.membership import Membership
    from app.models.notification import Notification
    from app.models.announcement import Announcement
    from app.models.role import Role


class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


# Keep Role enum for backward compatibility and quick checks
class RoleEnum(str, Enum):
    OG = "OG"  # Platform owner
    ADMIN = "ADMIN"  # Gym owner
    MEMBER = "MEMBER"
    TRAINER = "TRAINER"
    STAFF = "STAFF"

# Alias for backward compatibility
Role = RoleEnum


class User(SQLModel, table=True):

    __tablename__ = "users"
    
    id: str = Field(
        description="The user's id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    user_name: str = Field(
        description="The user's username",
        unique=True,
        min_length=4,
        max_length=72
    )
    name: str = Field(description="The user's name", min_length=4)
    email: str = Field(description="The user's email")
    password_hash: str = Field(description="The user's password hash", min_length=8)
    phone: str = Field(description="The user's phone number")
    gender: Gender = Field(description="The user's gender")
    address_line1: str = Field(description="The user's address line 1", min_length=4)
    address_line2: Optional[str] = Field(
        description="The user's address line 2",
        nullable=True
    )
    city: str = Field(description="The user's city", min_length=4)
    state: str = Field(description="The user's state", min_length=4)
    postal_code: str = Field(description="The user's postal code")
    country: str = Field(description="The user's country", min_length=4)
    dob: date = Field(description="The user's date of birth")
    photo_url: Optional[str] = Field(
        description="The user's photo URL",
        nullable=True
    )
    is_active: bool = Field(
        description="Whether the user is active",
        default=True
    )
    role_id: str = Field(
        description="The user's role id",
        foreign_key="roles.id",
        index=True
    )
    device_token: Optional[str] = Field(
        description="The user's device token for notifications",
        nullable=True
    )
    app_version: Optional[str] = Field(
        description="The app version the user is using",
        nullable=True
    )
    platform: Optional[str] = Field(
        description="The platform: android or ios",
        nullable=True
    )
    created_at: datetime = Field(
        description="The user's creation date",
        default_factory=datetime.now
    )
    gym_id: Optional[str] = Field(
        description="The gym id this user belongs to",
        foreign_key="gyms.id",
        nullable=True
    )
    
    # Relationships
    role_ref: Optional["Role"] = Relationship(back_populates="users")
    gym: Optional["Gym"] = Relationship(
        back_populates="members",
        sa_relationship_kwargs={"foreign_keys": "[User.gym_id]"}
    )
    owned_gyms: List["Gym"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "[Gym.owner_id]"}
    )
    attendances: List["Attendance"] = Relationship(back_populates="user")
    notifications: List["Notification"] = Relationship(back_populates="user")
    payments: List["Payment"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Payment.user_id]"}
    )
    verified_payments: List["Payment"] = Relationship(
        back_populates="verifier",
        sa_relationship_kwargs={"foreign_keys": "[Payment.verified_by]"}
    )
    announcements: List["Announcement"] = Relationship(back_populates="user")
    memberships: List["Membership"] = Relationship(back_populates="user")