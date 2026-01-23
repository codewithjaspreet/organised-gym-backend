from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AppInfoResponse(BaseModel):
    id: str
    platform: str
    android_app_version: str = Field(description="Android app version")
    ios_app_version: str = Field(description="iOS app version")
    android_maintenance_mode: bool = Field(description="Android maintenance mode status")
    ios_maintenance_mode: bool = Field(description="iOS maintenance mode status")
    created_at: datetime
    updated_at: Optional[datetime] = None


class AppInfoUpdate(BaseModel):
    platform: Optional[str] = Field(default=None, description="The platform identifier")
    android_app_version: Optional[str] = Field(default=None, description="Android app version")
    ios_app_version: Optional[str] = Field(default=None, description="iOS app version")
    android_maintenance_mode: Optional[bool] = Field(default=None, description="Android maintenance mode status")
    ios_maintenance_mode: Optional[bool] = Field(default=None, description="iOS maintenance mode status")
