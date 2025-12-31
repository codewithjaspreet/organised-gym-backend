from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime, date
from uuid import uuid4


class Membership(SQLModel, table=True):
    __tablename__ = "memberships"
    
    id: str = Field(
        description="The membership id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    user_id: str = Field(
        description="The user id",
        foreign_key="users.id"
    )
    gym_id: str = Field(
        description="The gym id",
        foreign_key="gyms.id"
    )
    start_date: date = Field(description="The membership start date")
    end_date: date = Field(description="The membership end date")
    status: str = Field(description="The membership status")
    plan_id: str = Field(
        description="The plan id",
        foreign_key="plans.id"
    )
    created_at: datetime = Field(
        description="The membership creation date",
        default_factory=datetime.now
    )
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="memberships")
    gym: Optional["Gym"] = Relationship(back_populates="memberships")
    plan: Optional["Plan"] = Relationship(back_populates="memberships")
    payments: List["Payment"] = Relationship(back_populates="membership")

