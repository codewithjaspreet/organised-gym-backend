from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


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

