from sqlmodel import Field, Relationship, SQLModel
from uuid import uuid4
from datetime import datetime
from typing import Optional

from app.models.gym import Gym
from app.models.user import User

class Announcement(SQLModel, table=True):
    __tablename__ = "announcements"
    
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)
    user_id: str = Field(foreign_key="users.id")
    gym_id:str = Field(foreign_key="gyms.id")
    user: Optional["User"] = Relationship(back_populates="announcements")
    gym: Optional["Gym"] = Relationship(back_populates="announcements")