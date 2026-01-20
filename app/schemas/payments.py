from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from app.schemas.user import CurrentPlanResponse


class PaymentCreate(BaseModel):
    user_id: str = Field(description="The user id")
    membership_id: str = Field(description="The membership id")
    gym_id: str = Field(description="The gym id")
    amount: Decimal = Field(description="The payment amount", ge=0)
    proof_url: Optional[str] = Field(description="The payment proof URL", nullable=True)
    status: str = Field(description="The payment status")
    verified_by: Optional[str] = Field(description="The user id who verified the payment", nullable=True)


class PaymentUpdate(BaseModel):
    amount: Optional[Decimal] = Field(description="The payment amount", nullable=True, ge=0)
    proof_url: Optional[str] = Field(description="The payment proof URL", nullable=True)
    status: Optional[str] = Field(description="The payment status", nullable=True)
    verified_by: Optional[str] = Field(description="The user id who verified the payment", nullable=True)


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    membership_id: str
    gym_id: str
    amount: Decimal
    proof_url: Optional[str] = None
    status: str
    verified_by: Optional[str] = None
    created_at: datetime


class MemberPaymentCreate(BaseModel):
    plan_id: str = Field(description="The plan id")
    proof_url: str = Field(description="The payment proof/screenshot URL")
    remarks: Optional[str] = Field(default=None, description="Payment remarks/notes", nullable=True)


class PaymentStatusType(str, Enum):
    APPROVE = "Approve"
    REJECT = "Reject"


class PaymentStatusUpdate(BaseModel):
    payment_id: str = Field(description="The payment id")
    status: PaymentStatusType = Field(description="Payment status: Approve or Reject")


class PendingPaymentResponse(BaseModel):
    """Response for pending payment with member details"""
    payment_id: str = Field(description="The payment id")
    user_id: str = Field(description="The user id who made the payment")
    proof_url: Optional[str] = Field(default=None, description="The payment proof URL")
    remarks: Optional[str] = Field(default=None, description="Payment remarks/notes")
    payment_at: str = Field(description="Payment creation date and time in Indian format (DD-MM-YYYY HH:MM:SS)")
    current_plan: Optional[CurrentPlanResponse] = Field(default=None, description="Current plan information for the member")


class PendingPaymentListResponse(BaseModel):
    """Paginated response for pending payments"""
    payments: List[PendingPaymentResponse] = Field(description="List of pending payments")
    total: int = Field(description="Total number of pending payments")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    has_next: bool = Field(description="Whether there are more pages")

