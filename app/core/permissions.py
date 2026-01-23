from fastapi import HTTPException, status, Depends
from typing import List
from sqlmodel import select, Session, and_, or_
from datetime import date
from app.core.dependencies import get_current_user, get_session
from datetime import date
from fastapi import Depends, HTTPException, status
from sqlmodel import select, and_
from app.models.gym import Gym
from app.models.gym_subscription import GymSubscription, SubscriptionStatus
from app.models.role import Role
from app.models.user import RoleEnum, User
from datetime import date
from fastapi import Depends, HTTPException, status
from sqlmodel import select, and_

from app.utils.fcm_notification import logger

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> User:

    logger.error(
        f"AUTH DEBUG | user_id={current_user.id} | "
        f"role_id={getattr(current_user, 'role_id', None)} | "
        f"user_dict={current_user.__dict__}"
    )


    logger.info(
        f"Auth check started | user_id={current_user.id} | "
        f"role_id={current_user.role_id} | path=protected"
    )

    if not current_user.is_active:
        logger.warning(f"User inactive | user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    if current_user.role_id:
        role = session.get(Role, current_user.role_id)
        logger.info(
            f"User role resolved | user_id={current_user.id} | role={role.name if role else None}"
        )

        if role and role.name in {
            RoleEnum.OG.value,
            "PLATFORM_ADMIN",
            "OG",
        }:
            logger.info(
                f"Bypassing subscription checks for platform admin | user_id={current_user.id}"
            )
            return current_user

    gym_id = current_user.gym_id
    logger.info(f"Initial gym_id | user_id={current_user.id} | gym_id={gym_id}")

    if not gym_id:
        gym = session.exec(
            select(Gym).where(Gym.owner_id == current_user.id)
        ).first()
        gym_id = gym.id if gym else None
        logger.info(
            f"Gym resolved via ownership | user_id={current_user.id} | gym_id={gym_id}"
        )

    # 4️⃣ Subscription check
    if gym_id:
        today = date.today()
        logger.info(
            f"Checking subscription | gym_id={gym_id} | date={today}"
        )

        active_subscription = session.exec(
            select(GymSubscription)
            .where(
                and_(
                    GymSubscription.gym_id == gym_id,
                    GymSubscription.status == SubscriptionStatus.ACTIVE,
                    GymSubscription.end_date >= today,
                )
            )
            .order_by(GymSubscription.end_date.desc())
        ).first()

        if not active_subscription:
            logger.error(
                f"OG plan expired or missing | user_id={current_user.id} | gym_id={gym_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "errorCode": "OG_PLAN_INACTIVE",
                    "message": "Your gym's OG plan has expired"
                }
            )

    logger.info(f"Auth success | user_id={current_user.id}")
    return current_user


def _get_user_role_name(current_user: User, session: Session) -> str:
    """Get the role name for a user from their role_id"""
    if not current_user.role_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User has no role assigned"
        )
    stmt = select(Role).where(Role.id == current_user.role_id)
    role = session.exec(stmt).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User role not found"
        )
    return role.name


def require_roles(*allowed_roles: RoleEnum):
    """Dependency factory to require specific roles"""
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
        session: Session = Depends(get_session)
    ) -> User:
        user_role_name = _get_user_role_name(current_user, session)
        allowed_role_names = [r.value for r in allowed_roles]
        if user_role_name not in allowed_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_role_names}"
            )
        return current_user
    return Depends(role_checker)


# Specific role dependencies
require_og = require_roles(RoleEnum.OG)
require_admin = require_roles(RoleEnum.ADMIN)
require_og_or_admin = require_roles(RoleEnum.OG, RoleEnum.ADMIN)
require_admin_or_staff = require_roles(RoleEnum.ADMIN, RoleEnum.STAFF)
require_any_authenticated = Depends(get_current_active_user)


def check_ownership_or_admin(user_id: str, current_user: User, session: Session) -> None:
    """Check if user is accessing their own resource or is admin"""
    user_role_name = _get_user_role_name(current_user, session)
    if user_id != current_user.id and user_role_name != RoleEnum.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own resources"
        )


def check_gym_ownership(gym_id: str, current_user: User, session: Session) -> None:
    """Check if user owns the gym or is OG"""
    from app.models.gym import Gym
    
    user_role_name = _get_user_role_name(current_user, session)
    if user_role_name == RoleEnum.OG.value:
        return  # OG can access any gym
    
    stmt = select(Gym).where(Gym.id == gym_id, Gym.owner_id == current_user.id)
    gym = session.exec(stmt).first()
    if not gym:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own gym"
        )

