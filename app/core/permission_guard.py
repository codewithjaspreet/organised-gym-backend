from fastapi import HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from typing import List
from app.core.dependencies import get_current_user
from app.db.db import get_session
from app.models.user import User
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.utils.response import failure_response


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the user is active"""
    if not current_user.is_active:
        # Return failure_response instead of raising exception
        from fastapi import Request
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "status": False,
                "message": "Inactive user",
                "data": None
            }
        )
    return current_user


def get_user_permissions(user: User, session: Session) -> List[str]:
    """
    Get all permission names for a user based on their role
    
    Args:
        user: The user object
        session: Database session
    
    Returns:
        List of permission names (e.g., ['user_create', 'user_get_all'])
    """
    # Get all permissions for the user's role
    stmt = (
        select(Permission.name)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id == user.role_id)
    )
    result = session.exec(stmt)
    return [perm for perm in result]


def require_permission(permission_name: str):
    """
    Dependency to require a specific permission
    
    Usage:
        @router.post("/users")
        def create_user(
            user: UserCreate,
            session: SessionDep,
            current_user: User = require_permission("user_create")
        ):
            ...
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        session: Session = Depends(get_session)
    ) -> User:
        # Get user permissions
        user_permissions = get_user_permissions(current_user, session)
        
        if permission_name not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission_name}"
            )
        
        return current_user
    
    return Depends(permission_dependency)


def require_any_permission(*permission_names: str):
    """
    Dependency to require at least one of the specified permissions
    
    Usage:
        @router.get("/users")
        def get_users(
            session: SessionDep,
            current_user: User = require_any_permission("user_get_all", "user_get_own")
        ):
            ...
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user),
        session: Session = Depends(get_session)
    ) -> User:
        user_permissions = get_user_permissions(current_user, session)
        
        if not any(perm in user_permissions for perm in permission_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required one of: {list(permission_names)}"
            )
        
        return current_user
    
    return Depends(permission_dependency)


def has_permission(user: User, permission_name: str, session: Session) -> bool:
    """
    Check if a user has a specific permission (for use in route logic)
    
    Args:
        user: The user object
        permission_name: The permission name to check
        session: Database session
    
    Returns:
        True if user has the permission, False otherwise
    """
    user_permissions = get_user_permissions(user, session)
    return permission_name in user_permissions

