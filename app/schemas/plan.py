from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    gym_id: str = Field(description="The gym id")
    name: str = Field(description="The plan name", min_length=1)
    duration_days: int = Field(description="The plan duration in days", ge=1)
    price: Decimal = Field(description="The plan price", ge=0)
    description: Optional[str] = Field(description="The plan description", nullable=True)
    is_active: bool = Field(description="Whether the plan is active", default=True)


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(description="The plan name", nullable=True)
    duration_days: Optional[int] = Field(description="The plan duration in days", nullable=True, ge=1)
    price: Optional[Decimal] = Field(description="The plan price", nullable=True, ge=0)
    description: Optional[str] = Field(description="The plan description", nullable=True)
    is_active: Optional[bool] = Field(description="Whether the plan is active", nullable=True)


class PlanResponse(BaseModel):
    id: str
    gym_id: str
    name: str
    duration_days: int
    price: Decimal
    description: Optional[str] = None
    is_active: bool
    created_at: datetime


class PlanListResponse(BaseModel):
    plans: List[PlanResponse] = Field(description="The list of plans")

