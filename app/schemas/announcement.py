from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class AnnouncementCreate(BaseModel):
    title: str = Field(description="The announcement title", min_length=1)
    message: str = Field(description="The announcement message", min_length=1)
    is_active: bool = Field(description="Whether the announcement is active", default=True)
    user_id: str = Field(description="The user id")
    gym_id: str = Field(description="The gym id")


class AnnouncementResponse(BaseModel):
    id: str = Field(description="The announcement id")
    title: str = Field(description="The announcement title")
    message: str = Field(description="The announcement message")
    is_active: bool = Field(description="Whether the announcement is active")
    user_id: str = Field(description="The user id")
    gym_id: str = Field(description="The gym id")
    created_at: datetime = Field(description="The announcement creation date")
    updated_at: datetime = Field(description="The announcement update date")


class AnnouncementListResponse(BaseModel):
    announcements: List[AnnouncementResponse] = Field(description="The list of announcements")

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(description="The announcement title", nullable=True)
    message: Optional[str] = Field(description="The announcement message", nullable=True)
    is_active: Optional[bool] = Field(description="Whether the announcement is active", nullable=True)
    user_id: Optional[str] = Field(description="The user id", nullable=True)
    gym_id: Optional[str] = Field(description="The gym id", nullable=True)