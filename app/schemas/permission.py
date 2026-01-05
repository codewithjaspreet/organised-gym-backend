from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PermissionCreate(BaseModel):
    name: str = Field(description="The permission's name (e.g., 'user_create')")
    resource: str = Field(description="The resource this permission applies to (e.g., 'user')")
    actions: str = Field(description="The actions allowed (e.g., 'create', 'read', 'update', 'delete')")
    description: Optional[str] = Field(description="Description of what this permission allows", default=None)


class PermissionResponse(BaseModel):
    id: str
    name: str
    resource: str
    actions: str
    description: Optional[str] = None
    created_at: datetime


class RoleCreate(BaseModel):
    name: str = Field(description="The role's name (e.g., 'OG', 'ADMIN')")
    description: Optional[str] = Field(description="Description of what this role represents", default=None)


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime


class RolePermissionCreate(BaseModel):
    role_id: str = Field(description="The role's id")
    permission_id: str = Field(description="The permission's id")


class RolePermissionResponse(BaseModel):
    id: str
    role_id: str
    permission_id: str
    created_at: datetime


class RoleWithPermissionsResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[PermissionResponse] = []
    created_at: datetime

