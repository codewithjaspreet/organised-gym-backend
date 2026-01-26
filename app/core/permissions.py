from fastapi import HTTPException, status, Depends
from sqlmodel import select, Session, and_
from datetime import date, timedelta
from app.core.dependencies import get_current_user, get_session
from app.models.gym import Gym
from app.models.gym_subscription import GymSubscription, SubscriptionStatus
from app.models.role import Role
from app.models.user import RoleEnum, User
from app.utils.fcm_notification import logger
from app.core.config import settings

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> User:
    """
    Validates that the current user is active and has a valid subscription or membership,
    including grace-period handling.
    """

    if not current_user.is_active:
        logger.warning(f"Inactive user | user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    role = session.get(Role, current_user.role_id) if current_user.role_id else None
    role_name = role.name if role else None

    if role_name in {RoleEnum.OG.value, "PLATFORM_ADMIN", "OG"}:
        return current_user

    today = date.today()
    grace_days = getattr(settings, "subscription_grace_period_days", 5)
    grace_period_start = today - timedelta(days=grace_days)

    gym_id = current_user.gym_id
    if not gym_id:
        gym = session.exec(
            select(Gym).where(Gym.owner_id == current_user.id)
        ).first()
        gym_id = gym.id if gym else None

    if gym_id:
        subscription = session.exec(
            select(GymSubscription)
            .where(
                and_(
                    GymSubscription.gym_id == gym_id,
                    GymSubscription.status == SubscriptionStatus.ACTIVE,
                    GymSubscription.end_date >= grace_period_start,
                )
            )
            .order_by(GymSubscription.end_date.desc())
        ).first()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "errorCode": "OG_PLAN_INACTIVE",
                    "message": "Your gym's OG plan has expired. Please renew your subscription to continue using the service.",
                },
            )

        if subscription.end_date < today:
            days_expired = (today - subscription.end_date).days
            if days_expired > grace_days:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "errorCode": "OG_PLAN_EXPIRED",
                        "message": (
                            f"Your gym's OG plan expired {days_expired} days ago. "
                            f"The {grace_days}-day grace period has ended. "
                            "Please renew your subscription to continue using the service."
                        ),
                    },
                )

    # 5️⃣ Member membership check
    if role_name == "MEMBER" and current_user.gym_id:
        from app.models.membership import Membership

        membership = session.exec(
            select(Membership)
            .where(
                and_(
                    Membership.user_id == current_user.id,
                    Membership.gym_id == current_user.gym_id,
                    Membership.status == "active",
                    Membership.end_date >= grace_period_start,
                )
            )
            .order_by(Membership.end_date.desc())
        ).first()

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "errorCode": "MEMBERSHIP_INACTIVE",
                    "message": "Your membership has expired. Please renew your membership to continue using the service.",
                },
            )

        if membership.end_date < today:
            days_expired = (today - membership.end_date).days
            if days_expired > grace_days:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "errorCode": "MEMBERSHIP_EXPIRED",
                        "message": (
                            f"Your membership expired {days_expired} days ago. "
                            f"The {grace_days}-day grace period has ended. "
                            "Please renew your membership to continue using the service."
                        ),
                    },
                )

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

