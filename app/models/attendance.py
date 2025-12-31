from sqlmodel import Field, SQLModel, Relationship
from typing import Optional
from datetime import datetime
from uuid import uuid4


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"
    
    id: str = Field(
        description="The attendance record id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    check_in_at: datetime = Field(description="The check-in timestamp")
    check_out_at: Optional[datetime] = Field(
        description="The check-out timestamp",
        nullable=True
    )
    user_id: str = Field(
        description="The user id",
        foreign_key="users.id"
    )
    gym_id: str = Field(
        description="The gym id",
        foreign_key="gyms.id"
    )
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="attendances")
    gym: Optional["Gym"] = Relationship(back_populates="attendances")

