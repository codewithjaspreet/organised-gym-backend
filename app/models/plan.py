from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.gym import Gym
    from app.models.membership import Membership


class Plan(SQLModel, table=True):
    __tablename__ = "plans"
    
    id: str = Field(
        description="The plan id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    gym_id: str = Field(
        description="The gym id",
        foreign_key="gyms.id"
    )
    name: str = Field(description="The plan name", min_length=1)
    duration_days: int = Field(description="The plan duration in days", ge=1)
    price: Decimal = Field(description="The plan price", ge=0)
    description: Optional[str] = Field(
        description="The plan description",
        nullable=True
    )
    is_active: bool = Field(
        description="Whether the plan is active",
        default=True
    )
    created_at: datetime = Field(
        description="The plan creation date",
        default_factory=datetime.now
    )
    
    # Relationships
    gym: Optional["Gym"] = Relationship(back_populates="plans")
    memberships: List["Membership"] = Relationship(back_populates="plan")

