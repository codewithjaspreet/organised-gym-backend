from datetime import datetime
from sqlmodel import select
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class GymCreate(BaseModel):
    owner_id: str = Field(description="The owner's user id (ADMIN role user)")
    name: str = Field(description="The gym's name", min_length=1)
    logo: Optional[str] = Field(description="The gym's logo URL", nullable=True)
    address_line1: str = Field(description="The gym's address line 1", min_length=4)
    address_line2: Optional[str] = Field(description="The gym's address line 2", nullable=True)
    city: str = Field(description="The gym's city", min_length=4)
    state: str = Field(description="The gym's state", min_length=4)
    postal_code: str = Field(description="The gym's postal code")
    country: str = Field(description="The gym's country", min_length=4)
    dob: Optional[str] = Field(description="The gym's date of birth", nullable=True)
    opening_hours: Optional[str] = Field(description="The gym's opening hours", nullable=True)
    is_active: bool = Field(description="Whether the gym is active", default=True)
    whatsapp_number: Optional[str] = Field(description="The gym's WhatsApp number", default=None)
    mobile_no: Optional[str] = Field(description="The gym's mobile number", default=None)
    website: Optional[str] = Field(description="The gym's website URL", default=None)
    email: Optional[str] = Field(description="The gym's email address", default=None)
    insta: Optional[str] = Field(description="The gym's Instagram handle/URL", default=None)
    facebook: Optional[str] = Field(description="The gym's Facebook page URL", default=None)
    youtube: Optional[str] = Field(description="The gym's YouTube channel URL", default=None)
    twitter: Optional[str] = Field(description="The gym's Twitter handle/URL", default=None)
    og_plan_id: str = Field(description="The OG plan id to assign to this gym (mandatory for platform admin)")


class GymUpdate(BaseModel):
    gym_id: Optional[str] = Field(default=None, description="The gym id (required for platform admin, optional for gym owner)")
    name: Optional[str] = Field(default=None, description="The gym's name")
    logo: Optional[str] = Field(default=None, description="The gym's logo URL")
    address_line1: Optional[str] = Field(default=None, description="The gym's address line 1")
    address_line2: Optional[str] = Field(default=None, description="The gym's address line 2")
    city: Optional[str] = Field(default=None, description="The gym's city")
    state: Optional[str] = Field(default=None, description="The gym's state")
    postal_code: Optional[str] = Field(default=None, description="The gym's postal code")
    country: Optional[str] = Field(default=None, description="The gym's country")
    dob: Optional[str] = Field(default=None, description="The gym's date of birth")
    opening_hours: Optional[str] = Field(default=None, description="The gym's opening hours")
    is_active: Optional[bool] = Field(default=None, description="Whether the gym is active")
    gym_code: Optional[str] = Field(default=None, description="The gym's code")
    whatsapp_number: Optional[str] = Field(default=None, description="The gym's WhatsApp number")
    mobile_no: Optional[str] = Field(default=None, description="The gym's mobile number")
    website: Optional[str] = Field(default=None, description="The gym's website URL")
    email: Optional[str] = Field(default=None, description="The gym's email address")
    insta: Optional[str] = Field(default=None, description="The gym's Instagram handle/URL")
    facebook: Optional[str] = Field(default=None, description="The gym's Facebook page URL")
    youtube: Optional[str] = Field(default=None, description="The gym's YouTube channel URL")
    twitter: Optional[str] = Field(default=None, description="The gym's Twitter handle/URL")
    og_plan_id: Optional[str] = Field(default=None, description="The OG plan id to assign/update for this gym (optional)")


class GymResponse(BaseModel):
    id: str
    owner_id: str
    name: str
    logo: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    dob: Optional[str] = None
    opening_hours: Optional[str] = None
    is_active: bool
    gym_code: Optional[str] = None
    whatsapp_number: Optional[str] = None
    mobile_no: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    insta: Optional[str] = None
    facebook: Optional[str] = None
    youtube: Optional[str] = None
    twitter: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GymListResponse(BaseModel):
    gyms: List[GymResponse]
