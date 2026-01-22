from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
from uuid import uuid4


class AppInfo(SQLModel, table=True):
    __tablename__ = "app_info"
    
    id: str = Field(
        description="The app info id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    platform: str = Field(
        description="The platform identifier",
        default="default"
    )
    android_app_version: str = Field(
        description="Android app version",
        default="1.0.0"
    )
    ios_app_version: str = Field(
        description="iOS app version",
        default="1.0.0"
    )
    android_maintenance_mode: bool = Field(
        description="Android maintenance mode status",
        default=False
    )
    ios_maintenance_mode: bool = Field(
        description="iOS maintenance mode status",
        default=False
    )
    created_at: datetime = Field(
        description="The creation date",
        default_factory=datetime.now
    )
    updated_at: Optional[datetime] = Field(
        description="The update date",
        nullable=True
    )
