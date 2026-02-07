from datetime import date, datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class MembershipCreate(BaseModel):
    user_id: str = Field(description="The user id")
    gym_id: str = Field(description="The gym id")
    start_date: date = Field(description="The membership start date")
    end_date: date = Field(description="The membership end date")
    status: str = Field(description="The membership status")
    plan_id: str = Field(description="The plan id")
    new_duration: Optional[int] = Field(default=None, description="New duration in days (replaces plan duration)")
    new_price: Optional[Decimal] = Field(default=None, description="New price (replaces plan price)")


class MembershipUpdate(BaseModel):
    start_date: Optional[date] = Field(description="The membership start date", nullable=True)
    end_date: Optional[date] = Field(description="The membership end date", nullable=True)
    status: Optional[str] = Field(description="The membership status", nullable=True)
    plan_id: Optional[str] = Field(description="The plan id", nullable=True)
    new_duration: Optional[int] = Field(default=None, description="New duration in days (replaces plan duration)", nullable=True)
    new_price: Optional[Decimal] = Field(default=None, description="New price (replaces plan price)", nullable=True)


class MembershipResponse(BaseModel):
    id: str
    user_id: str
    gym_id: str
    start_date: date
    end_date: date
    status: str
    plan_id: str
    new_duration: Optional[int] = None
    new_price: Optional[Decimal] = None
    created_at: datetime

