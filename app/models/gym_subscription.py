from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, date
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.gym import Gym
    from app.models.og_plan import OGPlan


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class GymSubscription(SQLModel, table=True):
    __tablename__ = "gym_subscriptions"
    
    id: str = Field(
        description="The gym subscription id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    gym_id: str = Field(
        description="The gym id",
        foreign_key="gyms.id"
    )
    og_plan_id: str = Field(
        description="The original plan id",
        foreign_key="og_plans.id"
    )
    start_date: date = Field(description="The subscription start date")
    end_date: date = Field(description="The subscription end date")
    status: SubscriptionStatus = Field(description="The subscription status")
    created_at: datetime = Field(
        description="The subscription creation date",
        default_factory=datetime.now
    )
    
    # Relationships
    gym: Optional["Gym"] = Relationship(back_populates="gym_subscriptions")
    og_plan: Optional["OGPlan"] = Relationship(back_populates="gym_subscriptions")

