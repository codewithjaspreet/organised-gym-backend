from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class DashboardKPIsResponse(BaseModel):
    active_members: int = Field(description="The number of active members")
    total_check_ins_today: int = Field(description="The total number of check-ins today")
    total_check_outs_today: int = Field(description="The total number of check-outs today")
    total_fee_due_members: int = Field(description="The total number of members with due fees")
    
    # Attendance Overview - Additional metrics
    absent_today_count: Optional[int] = Field(default=0, description="Number of members absent today")
    present_percentage: Optional[float] = Field(default=0.0, description="Percentage of members present today")
    present_today_trend_percentage: Optional[float] = Field(default=0.0, description="Trend percentage change in present members")
    
    # Fees & Revenue - Additional metrics
    total_fees_received_amount: Optional[Decimal] = Field(default=Decimal("0.0"), description="Total amount of fees received")
    total_fees_received_members_count: Optional[int] = Field(default=0, description="Number of members who paid fees")
    total_fees_pending_amount: Optional[Decimal] = Field(default=Decimal("0.0"), description="Total amount of fees pending")
    paid_percentage: Optional[float] = Field(default=0.0, description="Percentage of fees paid")
    unpaid_percentage: Optional[float] = Field(default=0.0, description="Percentage of fees unpaid")

class DashboardKPIsRequest(BaseModel):
    gym_id : str = Field(description="The gym id")

