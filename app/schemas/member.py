from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class AddMemberRequest(BaseModel):
    member_user_name: str = Field(description="The username of the member to add")
    gym_id: str = Field(description="The gym id to assign the member to")
    plan_id: Optional[str] = Field(default=None, description="The plan id for membership")
    new_duration: Optional[int] = Field(default=None, description="New duration in days (replaces plan duration)")
    new_price: Optional[Decimal] = Field(default=None, description="New price (replaces plan price)")
