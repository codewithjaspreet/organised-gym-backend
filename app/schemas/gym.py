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


class GymUpdate(BaseModel):
    name: Optional[str] = Field(description="The gym's name", nullable=True)
    logo: Optional[str] = Field(description="The gym's logo URL", nullable=True)
    address_line1: Optional[str] = Field(description="The gym's address line 1", nullable=True)
    address_line2: Optional[str] = Field(description="The gym's address line 2", nullable=True)
    city: Optional[str] = Field(description="The gym's city", nullable=True)
    state: Optional[str] = Field(description="The gym's state", nullable=True)
    postal_code: Optional[str] = Field(description="The gym's postal code", nullable=True)
    country: Optional[str] = Field(description="The gym's country", nullable=True)
    dob: Optional[str] = Field(description="The gym's date of birth", nullable=True)
    opening_hours: Optional[str] = Field(description="The gym's opening hours", nullable=True)
    is_active: Optional[bool] = Field(description="Whether the gym is active", nullable=True)


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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GymListResponse(BaseModel):
    gyms: List[GymResponse]
