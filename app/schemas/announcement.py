from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, field_serializer


class SendToType(str, Enum):
    ALL = "All"
    PENDING_FEES = "Pending Fees"
    BIRTHDAY = "Birthday"
    PLAN_EXPIRING_TODAY = "Plan Expiring Today"
    PLAN_EXPIRING_IN_3_DAYS = "Plan Expiring in 3 days"
    SPECIFIC_MEMBERS = "Specific Members"


class AnnouncementData(BaseModel):
    route: Optional[str] = Field(default="/gym-details", description="Deep link route for app navigation")


class AnnouncementCreate(BaseModel):
    title: str = Field(description="The announcement title", min_length=1)
    message: str = Field(description="The announcement message", min_length=1)
    is_active: bool = Field(description="Whether the announcement is active", default=True)
    user_id: str = Field(description="The user id")
    gym_id: str = Field(description="The gym id")
    send_to: SendToType = Field(description="Who to send the announcement to", default=SendToType.ALL)
    member_ids: Optional[List[str]] = Field(default=None, description="List of member user IDs (required when send_to is 'Specific Members')")
    data: Optional[AnnouncementData] = Field(default=None, description="Data object containing route for deep linking")


class AnnouncementResponse(BaseModel):
    id: str = Field(description="The announcement id")
    title: str = Field(description="The announcement title")
    message: str = Field(description="The announcement message")
    is_active: bool = Field(description="Whether the announcement is active")
    user_id: str = Field(description="The user id")
    gym_id: str = Field(description="The gym id")
    created_at: datetime = Field(description="The announcement creation date")
    updated_at: Optional[datetime] = Field(description="The announcement update date", default=None)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime_to_ist(self, value: Optional[datetime], _info) -> Optional[datetime]:
        """Convert naive UTC datetimes to Asia/Kolkata (IST) for API response."""
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Kolkata"))
        else:
            value = value.astimezone(ZoneInfo("Asia/Kolkata"))
        return value


class AnnouncementListResponse(BaseModel):
    announcements: List[AnnouncementResponse] = Field(description="The list of announcements")

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(description="The announcement title", nullable=True)
    message: Optional[str] = Field(description="The announcement message", nullable=True)
    is_active: Optional[bool] = Field(description="Whether the announcement is active", nullable=True)
    user_id: Optional[str] = Field(description="The user id", nullable=True)
    gym_id: Optional[str] = Field(description="The gym id", nullable=True)