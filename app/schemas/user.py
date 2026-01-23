from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.models.user import Gender



class UserCreate(BaseModel):
    user_name: Optional[str] = None  # Auto-generated if not provided
    name: str
    email: str
    password: str
    phone: str
    gender: Gender
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    dob: date
    gym_id: Optional[str] = None
    plan_id: Optional[str] = None
    role: str  # Role name: "PLATFORM_ADMIN", "ADMIN", "MEMBER", "TRAINER", "STAFF"
    device_token: Optional[str] = None
    app_version: Optional[str] = None
    platform: Optional[str] = None
    
    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v):
        if v is not None:
            v_lower = v.lower()
            if v_lower not in ["android", "ios"]:
                raise ValueError("Platform must be either 'android' or 'ios'")
            return v_lower
        return v

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[Gender] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None  # Role name
    gym_id: Optional[str] = None
    plan_id: Optional[str] = None

class CurrentPlanResponse(BaseModel):
    """Current plan information for member"""
    plan_id: str
    plan_name: str
    expiry_date: str
    monthly_price: float
    status: str
    days_left: int

class OGPlanInfoResponse(BaseModel):
    """OG Plan information for gym subscription"""
    og_plan_id: Optional[str] = None
    og_plan_name: Optional[str] = None
    og_plan_end_date: Optional[str] = None
    og_plan_status: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    user_name: str
    name: str
    email: str
    phone: str
    gender: Gender
    address_line1: str
    address_line2: Optional[str] = None
    gym_id: Optional[str] = None
    gym_name: Optional[str] = None
    plan_id: Optional[str] = None
    plan_amount: Optional[Decimal] = None
    current_plan: Optional[CurrentPlanResponse] = None
    og_plan: Optional[OGPlanInfoResponse] = None
    role_id: str
    role_name: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    created_at: datetime


class MemberListItemResponse(BaseModel):
    """Response for member list items with plan info"""
    id: str
    name: str
    email: str
    photo_url: Optional[str] = None
    plan_name: Optional[str] = None
    plan_status: Optional[str] = None
    plan_expiry_date: Optional[date] = None
    days_left: Optional[int] = None


class MemberDetailResponse(BaseModel):
    """Detailed member response for detail page"""
    id: str
    user_name: str
    name: str
    email: str
    phone: str
    gender: Gender
    dob: date
    photo_url: Optional[str] = None
    role: str
    
    # Current Plan Information
    current_plan: Optional[CurrentPlanResponse] = None
    
    # Personal Details
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    
    created_at: datetime


class MemberListResponse(BaseModel):
    members: List[MemberListItemResponse] = Field(description="The list of members")
    total: int = Field(description="Total number of members")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Number of items per page")
    has_next: bool = Field(description="Whether there are more pages")


class AvailableMemberResponse(BaseModel):
    """Simple response for available members (not assigned to any gym)"""
    id: str
    name: str
    email: str
    phone: str
    user_name: str


class AvailableMembersListResponse(BaseModel):
    members: List[AvailableMemberResponse] = Field(description="List of available members")


