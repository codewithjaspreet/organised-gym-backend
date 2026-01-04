from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.permission import Permission


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"
    
    id: str = Field(
        description="The role permission's id",
        primary_key=True,
        default_factory=lambda: str(uuid4())
    )
    role_id: str = Field(
        description="The role's id",
        foreign_key="roles.id",
        index=True
    )
    permission_id: str = Field(
        description="The permission's id",
        foreign_key="permissions.id",
        index=True
    )
    created_at: datetime = Field(
        description="The role permission's creation date",
        default_factory=datetime.now
    )
    
    # Relationships
    role: Optional["Role"] = Relationship(back_populates="role_permissions")
    permission: Optional["Permission"] = Relationship(back_populates="role_permissions")

