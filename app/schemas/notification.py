from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class SendToType(str, Enum):
    ALL = "All"
    PENDING_FEES = "Pending Fees"
    BIRTHDAY = "Birthday"
    PLAN_EXPIRING_TODAY = "Plan Expiring Today"
    PLAN_EXPIRING_IN_3_DAYS = "Plan Expiring in 3 days"


class NotificationCreate(BaseModel):
    gym_id: str = Field(description="The gym id")
    title: str = Field(description="The notification title", min_length=1)
    message: str = Field(description="The notification message", min_length=1)
    send_to: SendToType = Field(description="Who to send the notification to")
    screen: Optional[str] = Field(default="/notifications", description="Deep link route for app navigation")
    user_id: Optional[str] = Field(default=None, description="The user id (optional, for single user notifications)")


class NotificationResponse(BaseModel):
    id: str = Field(description="The notification id")
    user_id: str = Field(description="The user id")
    title: str = Field(description="The notification title")
    message: str = Field(description="The notification message")
    sent_at: datetime = Field(description="The notification sent at")
    status: str = Field(description="The notification status")


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse] = Field(description="The list of notifications")