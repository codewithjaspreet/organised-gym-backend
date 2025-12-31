from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.og_plan import BillingCycle


class OGPlanCreate(BaseModel):
    name: str = Field(description="The plan name", min_length=1)
    price: Decimal = Field(description="The plan price", ge=0)
    billing_cycle: BillingCycle = Field(description="The billing cycle")
    max_members: int = Field(description="Maximum number of members", ge=0)
    max_staff: int = Field(description="Maximum number of staff", ge=0)
    features: Dict[str, Any] = Field(description="The plan features")
    is_active: bool = Field(description="Whether the plan is active", default=True)


class OGPlanUpdate(BaseModel):
    name: Optional[str] = Field(description="The plan name", nullable=True)
    price: Optional[Decimal] = Field(description="The plan price", nullable=True, ge=0)
    billing_cycle: Optional[BillingCycle] = Field(description="The billing cycle", nullable=True)
    max_members: Optional[int] = Field(description="Maximum number of members", nullable=True, ge=0)
    max_staff: Optional[int] = Field(description="Maximum number of staff", nullable=True, ge=0)
    features: Optional[Dict[str, Any]] = Field(description="The plan features", nullable=True)
    is_active: Optional[bool] = Field(description="Whether the plan is active", nullable=True)


class OGPlanResponse(BaseModel):
    id: str
    name: str
    price: Decimal
    billing_cycle: BillingCycle
    max_members: int
    max_staff: int
    features: Dict[str, Any]
    is_active: bool
    created_at: datetime

