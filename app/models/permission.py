from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.role_permission import RolePermission


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"
    
    id: str = Field(
        description="The permission's id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    name: str = Field(
        description="The permission's name (e.g., 'user_create', 'user_get_all')",
        unique=True,
        index=True
    )
    resource: str = Field(
        description="The resource this permission applies to (e.g., 'user', 'gym', 'plan')",
        index=True
    )
    actions: str = Field(
        description="The actions allowed (e.g., 'create', 'read', 'update', 'delete', 'get_all')"
    )
    description: Optional[str] = Field(
        description="Description of what this permission allows",
        nullable=True
    )
    created_at: datetime = Field(
        description="The permission's creation date",
        default_factory=datetime.now
    )
    
    # Relationships
    role_permissions: List["RolePermission"] = Relationship(back_populates="permission")

