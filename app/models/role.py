from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.role_permission import RolePermission


class Role(SQLModel, table=True):
    __tablename__ = "roles"
    
    id: str = Field(
        description="The role's id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    name: str = Field(
        description="The role's name (e.g., 'OG', 'ADMIN', 'MEMBER')",
        unique=True,
        index=True
    )
    description: Optional[str] = Field(
        description="Description of what this role represents",
        nullable=True
    )
    created_at: datetime = Field(
        description="The role's creation date",
        default_factory=datetime.now
    )
    
    # Relationships
    users: List["User"] = Relationship(back_populates="role_ref")
    role_permissions: List["RolePermission"] = Relationship(back_populates="role")

