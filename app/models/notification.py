from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.user import User


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"
    
    id: str = Field(
        description="The notification id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    user_id: str = Field(
        description="The user id",
        foreign_key="users.id"
    )
    type: str = Field(description="The notification type")
    title: str = Field(description="The notification title", min_length=1)
    message: str = Field(description="The notification message", min_length=1)
    sent_at: datetime = Field(
        description="The timestamp when notification was sent",
        default_factory=datetime.now
    )
    status: str = Field(description="The notification status")
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="notifications")

