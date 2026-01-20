from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal


class DailyAttendanceResponse(BaseModel):
    """Daily attendance record for last 7 days"""
    date: str = Field(description="Date in Indian format (DD-MM-YYYY)")
    status: str = Field(description="Attendance status: 'present' or 'absent'")


class DashboardKPIsResponse(BaseModel):
    active_members: Optional[int] = Field(default=None, description="The number of active members")
    total_check_ins_today: Optional[int] = Field(default=None, description="The total number of check-ins today")
    total_check_outs_today: Optional[int] = Field(default=None, description="The total number of check-outs today")
    total_fee_due_members: Optional[int] = Field(default=None, description="The total number of members with due fees")
    
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
    
    # Member-specific metrics
    user_name: Optional[str] = Field(default=None, description="The user's username")
    name: Optional[str] = Field(default=None, description="The user's name")
    plan_id: Optional[str] = Field(default=None, description="The member's current plan ID from active membership")
    plan_amount: Optional[Decimal] = Field(default=None, description="The member's current plan amount from active membership")
    membership_expiry_date: Optional[str] = Field(default=None, description="Membership expiry date in Indian format (DD-MM-YYYY)")
    membership_days_remaining: Optional[int] = Field(default=None, description="Days remaining until membership expiry")
    last_7_days_attendance: Optional[List[DailyAttendanceResponse]] = Field(default=[], description="Last 7 days attendance streak")
    quote: Optional[str] = Field(default=None, description="Daily motivational quote based on day of month")
    check_in_time: Optional[str] = Field(default=None, description="Today's check-in time in Indian format (24hr clock)")
    checkout_time: Optional[str] = Field(default=None, description="Today's checkout time in Indian format (24hr clock)")
    focus: Optional[str] = Field(default=None, description="Today's workout focus")

class DashboardKPIsRequest(BaseModel):
    gym_id : str = Field(description="The gym id")

