from enum import Enum
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import JSON as SA_JSON
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.gym_subscription import GymSubscription


class BillingCycle(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    YEARLY = "YEARLY"
    LIFETIME = "LIFETIME"


class OGPlan(SQLModel, table=True):
    __tablename__ = "og_plans"
    
    id: str = Field(
        description="The original plan id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    name: str = Field(description="The plan name", min_length=1)
    price: Decimal = Field(description="The plan price", ge=0)
    billing_cycle: BillingCycle = Field(description="The billing cycle")
    max_members: int = Field(description="Maximum number of members", ge=0)
    max_staff: int = Field(description="Maximum number of staff", ge=0)
    features: Optional[Dict[str, Any]] = Field(
        description="The plan features",
        sa_column=Column(SA_JSON, nullable=True),
        default=None
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
    gym_subscriptions: List["GymSubscription"] = Relationship(back_populates="og_plan")

