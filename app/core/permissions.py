from fastapi import HTTPException, status, Depends
from typing import List
from app.core.dependencies import get_current_user
from app.models.user import User, Role


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_roles(*allowed_roles: Role):
    """Dependency factory to require specific roles"""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return Depends(role_checker)


# Specific role dependencies
require_og = require_roles(Role.OG)
require_admin = require_roles(Role.ADMIN)
require_og_or_admin = require_roles(Role.OG, Role.ADMIN)
require_admin_or_staff = require_roles(Role.ADMIN, Role.STAFF)
require_any_authenticated = Depends(get_current_active_user)


def check_ownership_or_admin(user_id: str, current_user: User) -> None:
    """Check if user is accessing their own resource or is admin"""
    if user_id != current_user.id and current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own resources"
        )


def check_gym_ownership(gym_id: str, current_user: User, session) -> None:
    """Check if user owns the gym or is OG"""
    from sqlmodel import select
    from app.models.gym import Gym
    
    if current_user.role == Role.OG:
        return  # OG can access any gym
    
    stmt = select(Gym).where(Gym.id == gym_id, Gym.owner_id == current_user.id)
    gym = session.exec(stmt).first()
    if not gym:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own gym"
        )

