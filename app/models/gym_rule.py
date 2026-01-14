from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.gym import Gym


class GymRule(SQLModel, table=True):
    __tablename__ = "gym_rules"
    
    id: str = Field(
        description="The rule's id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    gym_id: str = Field(
        description="The gym id",
        foreign_key="gyms.id",
        index=True
    )
    title: str = Field(description="The rule title", min_length=1)
    description: str = Field(description="The rule description", min_length=1)
    created_at: datetime = Field(
        description="The rule's creation date",
        default_factory=datetime.now
    )
    updated_at: Optional[datetime] = Field(
        description="The rule's update date",
        nullable=True
    )
    
    # Relationships
    gym: Optional["Gym"] = Relationship(back_populates="rules")
