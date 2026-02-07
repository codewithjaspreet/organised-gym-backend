from enum import Enum
from sqlmodel import JSON, Column, Field, Relationship, SQLModel
from uuid import uuid4
from datetime import datetime
from typing import Optional

from app.models.gym import Gym
from app.models.user import User


class SendToType(str, Enum):
    ALL = "All"
    SPECIFIC_MEMBERS = "Specific Members"
    BIRTHDAY = "Birthday"
    PENDING_FEES = "Pending Fees"
    PLAN_EXPIRING_TODAY = "Plan Expiring Today"
    PLAN_EXPIRING_IN_3_DAYS = "Plan Expiring in 3 days"
    ALL_USERS = "All Users"
    OWNERS = "Owners"
    MEMBERS = "Members"
    SPECIFIC_GYM = "Specific Gym"
    SPECIFIC_MEMBER = "Specific Member"

class Announcement(SQLModel, table=True):
    __tablename__ = "announcements"
    
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)
    user_id: str = Field(foreign_key="users.id")
    gym_id: Optional[str] = Field(default=None, foreign_key="gyms.id", nullable=True)
    user: Optional["User"] = Relationship(back_populates="announcements")
    gym: Optional["Gym"] = Relationship(back_populates="announcements")
    send_to: SendToType = Field(default=SendToType.ALL)
    member_ids: Optional[list[str]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
