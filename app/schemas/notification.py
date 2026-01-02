from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    user_id: str  = Field(description="The user id")
    title: str = Field(description="The notification title")
    message: str = Field(description="The notification message")


class NotificationResponse(BaseModel):
    id: str = Field(description="The notification id")
    user_id: str = Field(description="The user id")
    title: str = Field(description="The notification title")
    message: str = Field(description="The notification message")
    sent_at: datetime = Field(description="The notification sent at")
    status: str = Field(description="The notification status")


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse] = Field(description="The list of notifications")